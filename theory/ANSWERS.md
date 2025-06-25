# Theory Answers

In this section, I will walk through each of the theory questions from Part B.
---

## 1. Python Concurrency

When it comes to concurrency in a FastAPI microservice, I like to choose the right tool for the job:

- **`asyncio`**  
  - Best for I/O-bound work (database calls, network I/O).  
  - Single thread, cooperative multitasking.  
  - Example:  
    ```python
    async def fetch_data():
        response = await httpx.get("https://netskope.com")
        return response.json()
    ```
  - **Pros**: low overhead, handles many concurrent requests.  
  - **Cons**: everything shares one thread, not ideal for heavy CPU tasks.

- **Native threads (`threading`)**  
  - Good for blocking I/O and simple parallelism.  
  - Each thread shares memory but has its own call stack.  
  - Example:  
    ```python
    from threading import Thread

    def process_data(chunk):
        # some blocking operation
        print(chunk)

    t = Thread(target=process_data, args=(data_chunk,))
    t.start()
    ```
  - **Pros**: easy to use with blocking libraries.  
  - **Cons**: GIL limits true CPU parallelism; context-switch overhead.

- **Multiprocessing**  
  - Spawns separate processes—bypasses the GIL.  
  - Best for CPU-bound tasks (e.g., model inference).  
  - Example:  
    ```python
    from multiprocessing import Pool

    def cpu_intensive(x):
        return x*x

    with Pool(4) as p:
        results = p.map(cpu_intensive, data_chunks)
    ```
  - **Pros**: real parallelism, isolates memory.  
  - **Cons**: higher startup cost, IPC complexity.

**My takeaway**: Use **`asyncio`** for your HTTP endpoints and database calls, and offload heavy CPU work to a **process pool** or a dedicated worker.

---

## 2. LLM Cost Modeling

Running an open-source model on GPU-backed EC2 vs. a commercial API involves balancing capex and opex:

- **API-based (Opex)**  
  - Cost = `tokens_per_month * price_per_token`  
  - No infrastructure management, fully managed.

- **Self-hosted (Capex + Opex)**  
  - **Capex**: `GPU_purchase_cost / depreciation_months`  
  - **Opex**: `instance_hourly_rate * hours_per_month + power/cooling`  
  - **Total monthly** ≈ `Capex/mo + Opex`.

**Break-even analysis**:  
- Monthly_api = Tokens * API_price
- Monthly_self_hosted = (GPU_cost / Dep_months) + (hours * EC2_rate)
- Solve for Tokens where Monthly_self_hosted ≤ Monthly_api. Above that volume, it’s cheaper to self-host.

## 3. RAG Pipeline
Here’s how I designed the RAG pipeline for Scenario II:

1. **Ingestion** 
- Load JSON docs (supporting both single dict and list).
- Embed with a SentenceTransformer → normalize → index in FAISS.

2. **Query-time**
- Embed the user query → cosine search top-k docs.
- Stitch the top snippets into a concise “Based on these snippets…” answer.

3. **Citations**
- Return each source URL with a snippet preview for traceability.

4. **Why this way?**
- Speed: FAISS + in-memory = millisecond lookups.
- Simplicity: No extra services.
- Transparency: Every suggestion carries its origin.

5. **Next steps:**
- Upgrade to a hosted vector DB (Pinecone, Weaviate).
- Add a cross-encoder reranker for higher precision.
- Implement incremental or on-demand reindexing for changing docs.

## 4. RAG Evaluation
Measuring hallucination without human labels is challenging, but here’s a rough framework:

- **Self-consistency**: run the same prompt multiple times; measure response variance.
- **Citation recall**: track how often expected source docs appear in top-k.
- **Overlap score**: compare keyword overlap between answer and cited snippets; low overlap flags - potential hallucination.
- **Embedding distance**: flag answers drawn from docs with low similarity scores.

You can automate these checks to surface “risky” answers for manual review.

## 5. Prompt Injection Mitigation
I recommend a defense-in-depth approach:

- **Sanitize inputs**: strip control characters, enforce length limits.
- **System prompt locking**: use a fixed system instruction that user text can’t override.
- **Context window policing**: limit how much user history you feed into the model.
- **Output filtering**: scan for dangerous patterns (e.g., code snippets, SQL).
- **Policy & auditing**: log all prompts & responses, conduct periodic reviews.

Combining code-level checks, infra controls, and clear security policies helps guard against malicious or accidental prompt injection.