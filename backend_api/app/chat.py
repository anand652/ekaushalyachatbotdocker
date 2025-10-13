# backend_api/app/chat.py

from .processing import co, collection

def get_chatbot_response(query: str, company_id: int):
    """
    Queries the vector database for context and gets a response from Cohere's chat model,
    using the model's built-in RAG and citation features for accuracy.
    (This is the non-streaming version)
    """
    print(f"Received query for company_id: {company_id}")

    query_embedding = co.embed(
        texts=[query], model="embed-english-v3.0", input_type="search_query"
    ).embeddings

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=10,
        where={"company_id": company_id},
    )

    retrieved_metadata = results.get('metadatas', [[]])[0]
    
    if not retrieved_metadata:
        return "I'm sorry, I couldn't find any relevant information in the provided documents to answer your question."

    documents = [
        {
            "id": doc.get("chunk_id", f"doc_{i}"),
            "text": doc.get("text_chunk", ""),
            "filename": doc.get("filename", "Unknown Source")
        }
        for i, doc in enumerate(retrieved_metadata)
    ]

    preamble = """
    You are an expert Q&A assistant. Your goal is to provide clear, well-structured, and helpful answers based on the provided documents.
    When you answer, you MUST adhere to the following rules:
    1.  Provide a concise summary of the answer first.
    2.  Use markdown formatting, such as bullet points and bolding, to structure the detailed information for readability.
    3.  Synthesize information from all relevant sources to provide a comprehensive answer.
    4.  Do NOT make up information. Only use the information present in the provided documents.
    5.  You MUST cite your sources accurately for each piece of information.
    6.  If the documents do not contain the answer, clearly state that the information was not found.
    """

    response = co.chat(
        model="command-r-08-2024",
        message=query,
        documents=documents,
        preamble=preamble,
        prompt_truncation="AUTO",
        citation_quality="accurate"
    )

    answer = response.text
    
    if response.citations:
        cited_sources = set()
        for citation in response.citations:
            for doc_id in citation.document_ids:
                source_file = next((doc['filename'] for doc in documents if doc['id'] == doc_id), "Unknown Source")
                cited_sources.add(source_file)
        
        if cited_sources:
            answer += "\n\n**Sources:**\n" + "\n".join(f"- {source}" for source in sorted(list(cited_sources)))

    return answer


def get_chatbot_response_stream(query: str, company_id: int):
    """
    Queries the vector database for context and gets a streaming response from Cohere.
    (This is the new streaming version)
    """
    print(f"Received query for company_id: {company_id}")

    query_embedding = co.embed(
        texts=[query], model="embed-english-v3.0", input_type="search_query"
    ).embeddings

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=10,
        where={"company_id": company_id},
    )

    retrieved_metadata = results.get('metadatas', [[]])[0]
    
    if not retrieved_metadata:
        yield "I'm sorry, I couldn't find any relevant information in the provided documents to answer your question."
        return

    documents = [
        {
            "id": doc.get("chunk_id", f"doc_{i}"),
            "text": doc.get("text_chunk", ""),
            "filename": doc.get("filename", "Unknown Source")
        }
        for i, doc in enumerate(retrieved_metadata)
    ]

    preamble = """
    You are an expert Q&A assistant. Your goal is to provide clear, well-structured, and helpful answers based on the provided documents.
    When you answer, you MUST adhere to the following rules:
    1.  Provide a concise summary of the answer first.
    2.  Use markdown formatting, such as bullet points and bolding, to structure the detailed information for readability.
    3.  Synthesize information from all relevant sources to provide a comprehensive answer.
    4.  Do NOT make up information. Only use the information present in the provided documents.
    5.  You MUST cite your sources accurately for each piece of information.
    6.  If the documents do not contain the answer, clearly state that the information was not found.
    """

    response_stream = co.chat_stream(
        model="command-r-08-2024",
        message=query,
        documents=documents,
        preamble=preamble,
        prompt_truncation="AUTO",
        citation_quality="accurate"
    )

    cited_sources = set()

    # Iterate over the Cohere response stream
    for event in response_stream:
        # Check for text chunks and yield them to the client
        if event.event_type == "text-generation":
            yield event.text
        
        # Collect citations as they arrive
        elif event.event_type == "citation-generation":
            for citation in event.citations:
                for doc_id in citation.document_ids:
                    source_file = next((doc['filename'] for doc in documents if doc['id'] == doc_id), "Unknown Source")
                    cited_sources.add(source_file)
        
        # Stop iteration when the stream ends
        elif event.event_type == "stream-end":
            break

    # After the text has been streamed, yield the sources
    if cited_sources:
        yield "\n\n**Sources:**\n" + "\n".join(f"- {source}" for source in sorted(list(cited_sources)))