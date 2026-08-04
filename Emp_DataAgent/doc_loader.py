from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings   # local embedding model

CHROMA_DB = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# load the embedding model once (reused for every call)
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def load_text(file_path: str) -> str:
    """Load raw unstructured text from a PDF or DOCX."""
    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Only PDF or DOCX supported")

    docs = loader.load()
    return "\n".join(d.page_content for d in docs)


def embed_text(raw_text: str, employee_id: int, full_name: str):
    """Split raw text and store chunks in ChromaDB using HuggingFace embeddings."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)

    # attach metadata so we can filter by employee later
    metadatas = [{"employee_id": employee_id, "name": full_name} for _ in chunks]

    # open existing store if present, else it gets created on first add
    if Path(CHROMA_DB).exists():
        print("Chroma directory already exists")
        vector_db = Chroma(
            collection_name="resumes",
            persist_directory=CHROMA_DB,
            embedding_function=embedding_model,
        )
    else:
        vector_db = Chroma(
            collection_name="resumes",
            persist_directory=CHROMA_DB,
            embedding_function=embedding_model,
        )
        print("Vector store created..")

    # add the new chunks (works for both new and existing store)
    vector_db.add_texts(texts=chunks, metadatas=metadatas)
    return len(chunks)