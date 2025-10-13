# backend_api/app/processing.py

import os
import cohere
import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)
db_client = chromadb.PersistentClient(path="chroma_db")
collection = db_client.get_or_create_collection(name="company_documents")


def process_and_store_document(file_path: str, filename: str, company_id: int, document_id: int):
    """
    Reads a document (PDF or HTML/text), chunks it, creates embeddings, and stores them in ChromaDB.
    Works for both file uploads and URL ingestion.
    """
    print(f"Starting processing for document_id: {document_id}, filename: {filename}")

    try:
        # Determine file type by extension
        text = ""
        ext = filename.split('.')[-1].lower()

        if ext in ["pdf"]:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif ext in ["html", "htm", "txt"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if ext in ["html", "htm"]:
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
            else:  # txt
                text = content
        else:
            # Try generic text reading if unknown extension
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        if not text.strip():
            print(f"No text extracted from document_id: {document_id}")
            return

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        print(f"Document split into {len(chunks)} chunks.")

        # Create embeddings
        response = co.embed(
            texts=chunks, model="embed-english-v3.0", input_type="search_document"
        )
        embeddings = response.embeddings
        print("Embeddings created successfully.")

        # Prepare metadata for ChromaDB
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [{
            "company_id": company_id,
            "document_id": document_id,
            "filename": filename,
            "chunk_id": f"{document_id}_{i}",
            "text_chunk": chunk
        } for i, chunk in enumerate(chunks)]

        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
        print(f"Embeddings stored in ChromaDB for document_id: {document_id}")

    except Exception as e:
        print(f"An error occurred during processing for document_id {document_id}: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed temporary file: {file_path}")


def delete_document_from_chroma(document_id: int):
    """
    Deletes all document chunks from ChromaDB for a given document_id.
    """
    try:
        collection.delete(where={"document_id": document_id})
        print(f"Successfully deleted chunks for document_id: {document_id} from ChromaDB.")
    except Exception as e:
        print(f"Failed to delete chunks for document_id {document_id} from ChromaDB: {e}")