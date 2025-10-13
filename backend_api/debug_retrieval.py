# debug_retrieval.py

import os
import cohere
import chromadb
from dotenv import load_dotenv

def test_retrieval(test_query: str, company_id_to_test: int):
    """
    Directly queries ChromaDB to see what documents are being retrieved.
    """
    print("--- Starting Retrieval Test ---")

    # 1. Load environment and initialize clients
    load_dotenv()
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    if not COHERE_API_KEY:
        print("ERROR: Cohere API Key not found in .env file.")
        return

    co = cohere.Client(COHERE_API_KEY)
    db_client = chromadb.Client()
    collection = db_client.get_or_create_collection(name="company_documents")

    print(f"Testing for Company ID: {company_id_to_test}")
    print(f"Using test query: '{test_query}'")

    # 2. Embed the test query
    try:
        query_embedding = co.embed(
            texts=[test_query],
            model="embed-english-v3.0",
            input_type="search_query"
        ).embeddings
        print("Query embedded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to embed query. {e}")
        return

    # 3. Query the collection with the company_id filter
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5,
        where={"company_id": company_id_to_test}
    )

    # 4. Print the results
    documents = results.get('metadatas', [[]])[0]
    
    print(f"\n--- Found {len(documents)} relevant chunks ---")

    if not documents:
        print("\nConclusion: No matching documents were found. This is why the chatbot cannot answer.")
    else:
        for i, doc in enumerate(documents):
            print(f"\n--- Result {i+1} ---")
            print(f"Text Chunk: {doc.get('text_chunk', 'N/A')}")
            print("-----------------")
        print("\nConclusion: Retrieval is working! The text above is what the chatbot is using as context.")

if __name__ == "__main__":
    # --- CONFIGURE YOUR TEST HERE ---
    
    # Set this to the ID of the company whose documents you want to test.
    # You can find this ID in your 'companies' table in pgAdmin.
    COMPANY_ID_TO_TEST = 1 
    
    # IMPORTANT: Choose a sentence or a unique phrase that you know
    # exists inside the PDF you uploaded.
    TEST_QUERY = "What is the main topic of the document?" 

    test_retrieval(test_query=TEST_QUERY, company_id_to_test=COMPANY_ID_TO_TEST)