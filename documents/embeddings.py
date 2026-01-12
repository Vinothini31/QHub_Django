import os
import time
from typing import List
from django.conf import settings
import google.generativeai as genai

try:
    import chromadb
except Exception:
    chromadb = None

# -----------------------
# CONFIGURE GEMINI API KEY
# -----------------------
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

EMBED_MODEL_NAME = "models/text-embedding-004"

# -----------------------
# CHROMA DB DIRECTORY
# -----------------------
CHROMA_DIR = os.path.join(settings.BASE_DIR, "chroma_db")

# -----------------------
# GLOBAL CHROMA CLIENT (IMPORTANT FIX)
# -----------------------
_chroma_client = None


def get_chroma_client():
    global _chroma_client

    if not chromadb:
        return None

    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    return _chroma_client


# -----------------------
# TEXT CHUNKING
# -----------------------
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = end

    return chunks


# -----------------------
# GEMINI EMBEDDINGS
# -----------------------
def embed_texts(texts: List[str]) -> List[List[float]]:
    embeddings = []
    for i, t in enumerate(texts):
        print(f"🧠 Embedding chunk {i + 1}/{len(texts)}")
        result = genai.embed_content(
            model=EMBED_MODEL_NAME,
            content=t,
            task_type="retrieval_document"
        )
        embeddings.append(result["embedding"])
    return embeddings


# -----------------------
# UPSERT DOCUMENT EMBEDDINGS
# -----------------------
def upsert_document_embeddings(document, batch_size: int = 50):
    if not chromadb:
        print("Chroma not available; skipping embeddings")
        return

    print("🔥 UPSERT FUNCTION CALLED FOR DOC:", document.id)

    text = document.extracted_text or ""
    if not text.strip():
        print("⚠️ No text to embed")
        return

    client = get_chroma_client()
    if not client:
        return

    collection_name = f"document_{document.id}"

    try:
        collection = client.get_collection(name=collection_name)
    except chromadb.errors.NotFoundError:
        collection = client.get_or_create_collection(name=collection_name)
        print(f"ℹ️ Created new collection: {collection_name}")

    start = 0
    length = len(text)
    chunk_size = 1000
    overlap = 200
    chunk_index = 0

    batch_chunks = []
    batch_ids = []
    batch_metadatas = []

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]

        batch_chunks.append(chunk)
        batch_ids.append(f"{document.id}_{chunk_index}")
        batch_metadatas.append({
            "document_id": document.id,
            "chunk_index": chunk_index,
            "file_name": document.title
        })

        chunk_index += 1
        start = end - overlap
        if start < 0:
            start = end

        if len(batch_chunks) >= batch_size or start >= length:
            embeddings = embed_texts(batch_chunks)
            collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                metadatas=batch_metadatas,
                documents=batch_chunks
            )
            batch_chunks.clear()
            batch_ids.clear()
            batch_metadatas.clear()

    print(f"✅ Stored embeddings for document {document.id}")


# -----------------------
# QUERY DOCUMENT (RAG)
# -----------------------
def query_document(document_id: int, query: str, top_k: int = 5):
    client = get_chroma_client()
    if not client:
        return []

    try:
        collection = client.get_collection(name=f"document_{document_id}")
    except chromadb.errors.NotFoundError:
        print("❌ Collection not found")
        return []

    q_result = genai.embed_content(
        model=EMBED_MODEL_NAME,
        content=query,
        task_type="retrieval_query"
    )

    try:
        results = collection.query(
            query_embeddings=[q_result["embedding"]],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print("Query error:", e)
        return []

    output = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for i in range(len(docs)):
        output.append({
            "text": docs[i],
            "metadata": metas[i],
            "distance": dists[i],
            "file_name": metas[i].get("file_name")
        })
    print("🔎 Querying collection:", f"document_{document_id}")

    return output
