import json
import os

import pandas as pd
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from backend.config import settings
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.config"}:
        raise
    from config import settings


def load_documents(data_dir: str) -> list:
    """Load PDFs, text, CSV, Excel, and JSON files from a directory."""
    documents = []

    # Load files
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)

        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())

        elif filename.endswith(".txt"):
            loader = TextLoader(filepath)
            documents.extend(loader.load())

        elif filename.endswith(".csv"):
            loader = CSVLoader(filepath)
            documents.extend(loader.load())

        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            # Load Excel using pandas and convert to LangChain Documents
            df = pd.read_excel(filepath)
            # Convert each row to a string or a structured format
            for index, row in df.iterrows():
                content = " ".join([f"{col}: {val}" for col, val in row.items()])
                doc = Document(
                    page_content=content,
                    metadata={"source": filepath, "row": index},
                )
                documents.append(doc)

        elif filename.endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            if isinstance(json_data, list):
                for index, item in enumerate(json_data):
                    documents.append(
                        Document(
                            page_content=json.dumps(item),
                            metadata={"source": filepath, "item": index},
                        )
                    )
            else:
                documents.append(
                    Document(
                        page_content=json.dumps(json_data),
                        metadata={"source": filepath},
                    )
                )

    print(f"Loaded {len(documents)} total documents/rows from {data_dir}")
    return documents


def chunk_documents(documents: list) -> list:
    """
    Split documents into chunks.

    WHY RecursiveCharacterTextSplitter?
    - Tries to split at natural boundaries: paragraph  sentence  word
    - Smarter than splitting at exactly 500 chars (avoids cutting mid-sentence)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,  # 500 chars
        chunk_overlap=settings.chunk_overlap,  # 50 char overlap
        separators=["\n\n", "\n", ". ", " ", ""],  # priority order
    )

    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")
    return chunks


if __name__ == "__main__":
    import sys

    try:
        from backend.vector_store import ingest_to_store
    except ModuleNotFoundError:
        from vector_store import ingest_to_store

    data_dir = sys.argv[1] if len(sys.argv) > 1 else "./data"
    print(f" Loading documents from: {data_dir}")
    docs = load_documents(data_dir)

    if not docs:
        print("  No documents found. Add files to the data/ folder and re-run.")
        raise SystemExit(1)

    chunks = chunk_documents(docs)
    print(f" First chunk preview:\n{chunks[0].page_content[:200]}\n")

    ingest_to_store(chunks)
    print(" Ingestion complete  ChromaDB is ready for queries.")
