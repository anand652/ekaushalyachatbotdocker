#frontend_app/services/api_client.py

import os
import requests
from dotenv import load_dotenv

# Load the backend URL from the .env file
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
print("BACKEND_URL:", BACKEND_URL)

def login_user(email, password, company_id):
    """Sends login request to the backend API."""
    payload = {"email": email, "password": password, "company_id": company_id}
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        return None

def register_user(name, email, password, role, company_id):
    payload = {
        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "company_id": company_id
    }
    response = requests.post(f"{BACKEND_URL}/auth/register", json=payload)
    if response.status_code == 200:
        return response.json()
    return None

def upload_document(token: str, file):
    """Sends PDF document upload request to the backend API."""
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (file.name, file, file.type)}
    try:
        response = requests.post(f"{BACKEND_URL}/documents/upload", headers=headers, files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Upload failed: {e}")
        return None

def upload_url_document(token: str, url: str):
    """Sends a URL document upload request to the backend API."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"url": url}
    try:
        response = requests.post(f"{BACKEND_URL}/documents/upload_url", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Upload URL failed: {e}")
        return None

# New streaming function
def query_chatbot_stream(token: str, query: str):
    """Sends a chat query to the backend API and yields streamed responses."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": query}
    try:
        # Use stream=True to keep the connection open and receive chunks
        with requests.post(f"{BACKEND_URL}/chat/query_stream", headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            # Iterate over the response content, line by line
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                yield chunk
    except requests.exceptions.RequestException as e:
        print(f"Query failed: {e}")
        yield "Sorry, I couldn't get a response. Please try again."

def get_companies():
    """Fetches the list of all companies from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/companies/")
        response.raise_for_status()
        print("Companies response:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to get companies: {e}")
        return []

def get_documents(token: str):
    """Fetch all documents for the current admin's company"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BACKEND_URL}/documents/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch documents: {e}")
        return []

def download_document(token: str, document_id: int):
    """Download PDF bytes from backend"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BACKEND_URL}/documents/download/{document_id}", headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Failed to download document {document_id}: {e}")
        return None

def delete_document(token: str, document_id: int):
    """Sends a delete document request to the backend API."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"{BACKEND_URL}/documents/delete/{document_id}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to delete document {document_id}: {e}")
        return False