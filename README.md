You are a senior Python engineer. Generate a complete, working offline RAG system that ingests PDF documents and answers questions only from those docs, with citations and anti-hallucination guardrails.

Hard requirements

1. Offline only: no cloud APIs. Use local models only.


2. Input docs: PDFs stored in data/pdfs/


3. Must handle text-heavy enterprise PDFs (70–100+ pages each).


4. Provide accurate answers with citations (doc name + page number + chunk id).


5. If answer is not explicitly supported by retrieved text, the system must respond:
“Not found in provided documents.”
and show the closest relevant citations instead of guessing.


6. Retrieval must be hybrid:

Vector similarity search (FAISS)

Keyword search (BM25)

Merge & dedupe candidates



7. Must include reranking step (cross-encoder reranker from sentence-transformers) to improve relevance.


8. Must include a verification pass: check every answer sentence is supported by retrieved chunks; remove unsupported claims; if insufficient support → “Not found”.


9. Provide CLI commands:

python ingest.py to build index

python query.py "question..." to ask

python query.py --interactive interactive mode



10. Persist everything to disk under data/index/ so query is fast.



Tech constraints / Libraries

Use these libraries:

PDF extraction: pymupdf (fitz)

Embeddings: sentence-transformers

Vector store: faiss-cpu

BM25: rank-bm25

Reranker: sentence-transformers CrossEncoder

Standard libs: json, pathlib, argparse, hashlib, logging, etc.


Assume models are available locally. Use defaults but allow override via env vars:

EMBED_MODEL default sentence-transformers/all-MiniLM-L6-v2

RERANK_MODEL default cross-encoder/ms-marco-MiniLM-L-6-v2


Project structure to generate

Create this exact structure with code in each file:

rag_offline/
  data/pdfs/                # user drops PDFs here
  data/index/               # generated indexes
  ingest.py
  query.py
  requirements.txt
  README.md
  rag/
    __init__.py
    pdf_loader.py
    text_cleaner.py
    chunker.py
    embedder.py
    faiss_store.py
    bm25_store.py
    reranker.py
    retriever.py
    prompts.py
    answerer.py
    verifier.py
    utils.py

Detailed behavior specifications

Ingestion (ingest.py)

Walk all PDFs in data/pdfs/

For each PDF:

Extract text per page with fitz

Clean text (remove repeated whitespace, normalize)

Chunk per page using structure-aware heuristic:

Prefer splitting on paragraph breaks and headings-like lines

Keep bullets together when possible

Use safe fallback: character-based chunking if structure fails


Each chunk must store metadata:

doc_name, doc_path, doc_hash, page, chunk_id, text



Embed each chunk using SentenceTransformer with normalize_embeddings=True

Build FAISS index using cosine similarity (IndexFlatIP)

Build BM25 index from all chunk texts

Save:

vectors.faiss

meta.jsonl (one JSON per chunk, includes text + metadata)

bm25.json (tokenized docs or necessary data to reconstruct BM25)

manifest.json containing doc hashes and counts


Support incremental indexing:

If a PDF hash unchanged, do not re-embed (skip)

If changed/new, reprocess only that doc and rebuild index (simple rebuild acceptable)



Retrieval (rag/retriever.py)

Given a user question:

1. Create N=4 query variants (simple deterministic expansion):

original question

keywords-only version (drop stopwords)

version with synonyms placeholders (minimal)

version with “section/definition” focus (Do NOT call online services.)



2. For each query variant:

vector search topK=40

BM25 search topK=40



3. Merge candidates (dedupe by chunk_id), keep best combined score


4. Rerank merged candidates using CrossEncoder; take top 8


5. Return top chunks with metadata and rerank scores



Answering (rag/answerer.py)

Build context from top chunks (include doc/page/chunk_id headers)

Use a strict prompt template from rag/prompts.py:

“Use only the provided context”

“Cite sources for every bullet”

“If missing, say Not found”


Since we’re offline and may not have an LLM, implement two modes:

1. Default mode (no LLM): extractive answer:

Return top relevant passages + short summary



2. If OLLAMA_URL env var present, call local Ollama HTTP API for generation:

Provide code to call Ollama (POST /api/generate) with model name from OLLAMA_MODEL

Use streaming=false for simplicity




Output format:

Answer: bullet list

Citations: each bullet lists doc/page/chunk_id

Supporting excerpts: show 1–2 short excerpts (max 300 chars) per citation



Verification (rag/verifier.py)

Take generated answer bullets and retrieved chunks

For each bullet:

check that at least one chunk has substantial lexical overlap or contains key phrases

if not supported, drop the bullet


If all bullets dropped:

respond “Not found in provided documents.”

include top 3 closest chunks as “Closest references”



Query CLI (query.py)

Load FAISS + meta + BM25 from disk

Run retrieval + rerank

Generate answer + verification

Print final response cleanly

--interactive loop


Logging

Add helpful logs: indexing counts, retrieval stats, rerank time


Deliverables

1. Full code for all files


2. requirements.txt


3. README.md with:

install steps

how to run ingestion

how to query

environment variables

notes on accuracy and “not found” behavior




Now generate the entire project code accordingly. Ensure it runs end-to-end locally.
