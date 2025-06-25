# app/rag.py
import os
import json
import time
import faiss
from sentence_transformers import SentenceTransformer
from app.config import DATA_DIR

# 1) Embed model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
embedding_dim = embed_model.get_sentence_embedding_dimension()

# Globals for FAISS index and docs
index: faiss.IndexFlatIP | None = None
doc_ids: list[str] = []
doc_texts: list[str] = []

def ingest_documents_from_data(data_dir: str = DATA_DIR):
    """
    Load JSON docs (each file may be a dict or a list of dicts) and build a FAISS index.
    """
    global index, doc_ids, doc_texts

    doc_ids = []
    doc_texts = []

    for fname in os.listdir(data_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(data_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # normalize to a list of records
        records = data if isinstance(data, list) else [data]
        for rec in records:
            url = rec.get("url")
            content = rec.get("content", "").strip()
            if url and content:
                doc_ids.append(url)
                doc_texts.append(content)

    if not doc_texts:
        index = None
        return

    # 2) Compute embeddings
    embeddings = embed_model.encode(doc_texts, convert_to_numpy=True)
    # 3) Normalize to unit length for cosine
    faiss.normalize_L2(embeddings)
    # 4) Build FAISS index (inner-product)
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(embeddings)

def generate_response(query: str, k: int = 5):
    """
    Embed the query, search FAISS, and return a simple snippet-based answer.
    """
    if index is None or not doc_ids:
        return "No documents indexed.", [], {"tokens_in": 0, "tokens_out": 0, "retrieval_ms": 0}

    t0 = time.time()
    q_emb = embed_model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)

    D, I = index.search(q_emb, k)
    retrieval_ms = int((time.time() - t0) * 1000)

    hits = I[0]
    docs = [doc_texts[i] for i in hits]
    sources = [doc_ids[i] for i in hits]

    context = "\n\n".join(docs)
    answer = f"Based on these snippets:\n\n{context[:500]}..."
    citations = [
        {"source": src, "snippet": txt[:200]}
        for src, txt in zip(sources, docs)
    ]
    stats = {
        "tokens_in": len(query.split()),
        "tokens_out": len(answer.split()),
        "retrieval_ms": retrieval_ms
    }
    return answer, citations, stats
