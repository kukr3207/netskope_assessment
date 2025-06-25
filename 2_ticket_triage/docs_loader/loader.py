import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import time
import json
import re
from pathlib import Path
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

BASE_URL = "https://docs.netskope.com/"
DATA_DIR = os.getenv("DATA_DIR", "data")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")

class NetskopeDocsCrawler:
    def __init__(self, base_url=BASE_URL, data_dir=DATA_DIR, use_selenium=True):
        self.base_url = base_url
        self.data_dir = data_dir
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        
        # Create data directory
        Path(self.data_dir).mkdir(exist_ok=True)
        
        # Load existing metadata
        self.metadata = self.load_metadata()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for JavaScript-heavy pages"""
        if self.driver:
            return
            
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            print("Falling back to requests-only mode")
            self.use_selenium = False
    
    def load_metadata(self):
        """Load existing crawl metadata"""
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"crawled_urls": {}, "last_crawl": None}
    
    def save_metadata(self):
        """Save crawl metadata"""
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
    
    def is_valid_docs_url(self, url):
        """Check if URL is a valid documentation page"""
        parsed = urlparse(url)
        
        # Must be from the same domain
        if parsed.netloc != urlparse(self.base_url).netloc:
            return False
        
        # Skip non-documentation URLs
        skip_patterns = [
            r'/api/',
            r'/login',
            r'/logout',
            r'/search',
            r'\.pdf$',
            r'\.zip$',
            r'\.jpg$',
            r'\.png$',
            r'\.gif$',
            r'#',  # Skip anchor links
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def extract_content_with_requests(self, url):
        """Extract content using requests + BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try multiple content selectors for different doc site layouts
            content_selectors = [
                '.main-content',
                '.content',
                '.documentation-content',
                '.docs-content',
                'article',
                '.article-content',
                '#main-content',
                '.page-content',
                'main',
                '.container .content'
            ]
            
            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if not content_div:
                content_div = soup.find('body')
            
            if not content_div:
                return None, None
            
            # Extract title
            title = None
            title_selectors = ['h1', '.page-title', '.title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract clean text
            text = content_div.get_text(separator=' ', strip=True)
            
            # Clean up the text
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return title, text
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None, None
    
    def extract_content_with_selenium(self, url):
        """Extract content using Selenium for JavaScript-heavy pages"""
        try:
            self.driver.get(url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try multiple content selectors
            content_selectors = [
                '.main-content',
                '.content',
                '.documentation-content',
                '.docs-content',
                'article',
                '.article-content',
                '#main-content',
                '.page-content',
                'main'
            ]
            
            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if not content_div:
                content_div = soup.find('body')
            
            if not content_div:
                return None, None
            
            # Extract title
            title = None
            try:
                title = self.driver.title
            except:
                title_elem = soup.select_one('h1')
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Extract clean text
            text = content_div.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return title, text
            
        except Exception as e:
            print(f"Error extracting content from {url} with Selenium: {e}")
            return None, None
    
    def find_links(self, url, soup):
        """Find all documentation links on a page"""
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Convert relative URLs to absolute
            full_url = urljoin(url, href)
            
            # Clean URL (remove fragments, query params that don't matter)
            parsed = urlparse(full_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if self.is_valid_docs_url(clean_url):
                links.add(clean_url)
        
        return links
    
    def crawl_docs(self, max_pages=1000, delay=1):
        """Main crawling function"""
        print(f"Starting crawl of {self.base_url}")
        
        if self.use_selenium:
            self.setup_selenium()
            if not self.driver:
                print("Selenium setup failed, using requests only")
        
        to_visit = [self.base_url]
        visited = set()
        docs = []
        
        try:
            while to_visit and len(visited) < max_pages:
                url = to_visit.pop(0)
                
                if url in visited:
                    continue
                
                print(f"Crawling ({len(visited)+1}/{max_pages}): {url}")
                
                # Extract content
                if self.use_selenium and self.driver:
                    title, text = self.extract_content_with_selenium(url)
                else:
                    title, text = self.extract_content_with_requests(url)
                
                if not text or len(text.strip()) < 50:
                    print(f"  Skipping - insufficient content")
                    visited.add(url)
                    continue
                
                visited.add(url)
                
                # Store document
                doc_data = {
                    'url': url,
                    'title': title or 'Untitled',
                    'content': text,
                    'content_length': len(text),
                    'crawl_timestamp': time.time()
                }
                
                docs.append(doc_data)
                
                # Save individual file
                self.save_document(doc_data)
                
                # Find new links (use requests for link extraction to be faster)
                try:
                    if self.use_selenium and self.driver:
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    else:
                        response = self.session.get(url, timeout=10)
                        soup = BeautifulSoup(response.text, 'html.parser')
                    
                    new_links = self.find_links(url, soup)
                    
                    for link in new_links:
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)
                    
                    print(f"  Found {len(new_links)} links, queue size: {len(to_visit)}")
                    
                except Exception as e:
                    print(f"  Error finding links: {e}")
                
                # Respectful delay
                time.sleep(delay)
                
        finally:
            if self.driver:
                self.driver.quit()
        
        # Update metadata
        self.metadata['last_crawl'] = time.time()
        self.metadata['total_pages'] = len(docs)
        self.save_metadata()
        
        print(f"\nCrawl complete! Processed {len(docs)} pages")
        return docs
    
    def save_document(self, doc_data):
        """Save a single document to file"""
        # Create filename from URL
        parsed = urlparse(doc_data['url'])
        filename = parsed.path.strip('/').replace('/', '_') or 'index'
        
        # Add hash to handle duplicates
        url_hash = hashlib.md5(doc_data['url'].encode()).hexdigest()[:8]
        filename = f"{filename}_{url_hash}"
        
        # Save as JSON for structured data
        json_path = os.path.join(self.data_dir, f"{filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        # Also save as plain text for simple RAG ingestion
        txt_path = os.path.join(self.data_dir, f"{filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Title: {doc_data['title']}\n")
            f.write(f"URL: {doc_data['url']}\n\n")
            f.write(doc_data['content'])
    
    def create_rag_index(self):
        """Create a simple index file for RAG systems"""
        index_data = []
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and filename != 'metadata.json':
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        index_data.append({
                            'filename': filename,
                            'url': doc_data['url'],
                            'title': doc_data['title'],
                            'content_length': doc_data['content_length'],
                            'crawl_timestamp': doc_data.get('crawl_timestamp')
                        })
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        
        # Save index
        index_path = os.path.join(self.data_dir, 'rag_index.json')
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
        
        print(f"Created RAG index with {len(index_data)} documents")
        return index_path

def main():
    # Configuration
    MAX_PAGES = int(os.getenv("MAX_PAGES", "500"))
    DELAY = float(os.getenv("CRAWL_DELAY", "1.0"))
    USE_SELENIUM = os.getenv("USE_SELENIUM", "true").lower() == "true"
    
    print(f"Configuration:")
    print(f"  Max pages: {MAX_PAGES}")
    print(f"  Delay: {DELAY}s")
    print(f"  Use Selenium: {USE_SELENIUM}")
    
    crawler = NetskopeDocsCrawler(use_selenium=USE_SELENIUM)
    
    start_time = time.time()
    docs = crawler.crawl_docs(max_pages=MAX_PAGES, delay=DELAY)
    elapsed = time.time() - start_time
    
    print(f"\nCrawling completed in {elapsed:.1f}s")
    print(f"Successfully crawled {len(docs)} pages")
    
    # Create RAG index
    crawler.create_rag_index()
    
    # Print summary
    total_content = sum(doc['content_length'] for doc in docs)
    print(f"Total content: {total_content:,} characters")
    print(f"Average content per page: {total_content // len(docs):,} characters")
    print(f"Data saved to: {crawler.data_dir}")

if __name__ == '__main__':
    main()