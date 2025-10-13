#frontend_app/app.py

import streamlit as st
import jwt
from services import api_client

st.set_page_config(page_title="Company Chatbot", layout="wide")

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}            /* Hides hamburger */
    footer {visibility: hidden;}                /* Hides footer */
    [data-testid="stCloudStatusWidget"] {display: none !important;}  /* Hides Deploy button */
    button[kind="header"] {display: none !important;}              /* Extra safety */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Initialize session state ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Helper: Show user info top-right ---
def show_user_info():
    cols = st.columns([8, 2])
    with cols[1]:
        if st.session_state.get("logged_in"):
            user_display = st.session_state.get("user_name") or st.session_state.get("token_email")
            role = st.session_state.get("role")
            company = st.session_state.get("company_name", "")
            st.markdown(f"**{user_display} - {company}**")

# --- Sidebar ---
with st.sidebar:
    if not st.session_state.get("logged_in"):
        if st.button("Login"):
            st.session_state.page = "login"
            st.rerun()
        if st.button("Signup"):
            st.session_state.page = "signup"
            st.rerun()
    else:
        if st.session_state.get("role") == "admin":
            if st.button("Admin Dashboard"):
                st.session_state.page = "admin"
                st.rerun()
        elif st.session_state.get("role") == "user":
            if st.button("User Chat"):
                st.session_state.page = "chat"
                st.rerun()

        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.page = "login"
            st.rerun()

# --- Pages ---
if st.session_state.page == "home":
    show_user_info()
    st.title("Welcome to the ekaushalya Chatbot Portal")
    st.write("Please log in or sign up to continue.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assests/images/ai.jpg", width=300)

elif st.session_state.page == "login":
    show_user_info()
    st.markdown("<h2 style='text-align:center;'>Login</h2>", unsafe_allow_html=True)

    companies = api_client.get_companies()
    if companies:
        company_options = {comp['name']: comp['id'] for comp in companies}
        selected_company_name = st.selectbox("Select your company", options=company_options.keys())
        selected_company_id = company_options[selected_company_name]

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if email and password and selected_company_id:
                response_data = api_client.login_user(email, password, selected_company_id)

                if response_data:
                    token = response_data.get('access_token')
                    st.session_state.logged_in = True
                    st.session_state.token = token

                    user_info = jwt.decode(token, options={"verify_signature": False})
                    st.session_state.role = user_info.get('role')
                    st.session_state.user_name = user_info.get('name')
                    st.session_state.company_name = selected_company_name

                    st.success("Login successful!")
                    st.session_state.page = "admin" if st.session_state.role == "admin" else "chat"
                    st.rerun()
                else:
                    st.error("Invalid credentials for the selected company.")
            else:
                st.warning("Please enter all details.")
    else:
        st.error("Could not load company list. Please ensure the backend is running.")

elif st.session_state.page == "signup":
    show_user_info()
    st.markdown("<h2 style='text-align:center;'>Create an Account</h2>", unsafe_allow_html=True)

    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    role = st.selectbox("Register as", ["admin", "user"])

    companies = api_client.get_companies()
    if companies:
        company_options = {comp['name']: comp['id'] for comp in companies}
        selected_company_name = st.selectbox("Select your company", options=company_options.keys())
        company_id = company_options[selected_company_name]
    else:
        st.error("Could not load company list.")
        company_id = None

    if st.button("Signup", use_container_width=True):
        if not (name and email and password and confirm_password and company_id):
            st.error("Please fill all fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            response_data = api_client.register_user(name, email, password, role, company_id)
            if response_data:
                st.success("User registered successfully! Please login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("Registration failed. Email may already exist.")

elif st.session_state.page == "admin":
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
        st.error("You are not authorized to view this page. Please login as an admin.")
        st.stop()

    show_user_info()
    company_name = st.session_state.get("company_name", "Company")
    st.title(f"{company_name} Admin Dashboard")
    st.write(f"Welcome, {st.session_state.get('user_name') or 'Admin'}!")

    st.subheader("Upload Documents")

    # PDF Upload
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file and st.button("Upload PDF"):
        token = st.session_state.get('token')
        if token:
            with st.spinner("Uploading and processing PDF..."):
                response = api_client.upload_document(token, uploaded_file)
                if response:
                    st.success(f"Successfully uploaded '{uploaded_file.name}'!")
                    st.rerun()
                else:
                    st.error("PDF upload failed. Please check backend logs.")

    # URL Upload
    url_input = st.text_input("Or enter a URL to process")
    if url_input and st.button("Upload URL"):
        token = st.session_state.get('token')
        if token:
            with st.spinner("Fetching and processing URL..."):
                response = api_client.upload_url_document(token, url_input)
                if response:
                    st.success(f"Successfully processed URL: {url_input}")
                    st.rerun()
                else:
                    st.error("URL upload failed. Please check backend logs.")

    st.subheader("Uploaded Documents")
    token = st.session_state.get('token')
    documents = []
    if token:
        documents = api_client.get_documents(token)

    if documents:
        for doc in documents:
            cols = st.columns([6, 2, 2])
            
            # Display filename
            cols[0].write(doc["filename"])
            
            # Conditionally render Download button or URL link
            if doc.get("content_type") == "application/pdf":
                # Render download button for PDFs
                pdf_bytes = api_client.download_document(token, doc["id"])
                if pdf_bytes:
                    cols[1].download_button(
                        label="Download",
                        data=pdf_bytes,
                        file_name=doc["filename"],
                        mime="application/pdf"
                    )
            elif doc.get("source_url"): # Check for the new source_url field
                # Render a clickable URL for URL documents
                cols[1].markdown(f"[View URL]({doc['source_url']})", unsafe_allow_html=True)
            else:
                # Default case for other file types
                cols[1].write("")  # Empty column to align Delete button
            
            # Delete button (remains the same)
            if cols[2].button("Delete", key=f"delete_btn_{doc['id']}"):
                with st.spinner(f"Deleting '{doc['filename']}'..."):
                    success = api_client.delete_document(token, doc["id"])
                    if success:
                        st.success(f"Successfully deleted '{doc['filename']}'.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete '{doc['filename']}'.")
    else:
        st.info("No documents uploaded yet.")

elif st.session_state.page == "chat":
    if not st.session_state.get("logged_in") or (
        st.session_state.get("role") not in ["user", "admin"]
    ):
        st.error("You are not authorized to view this page. Please login.")
        st.stop()

    show_user_info()
    company_name = st.session_state.get("company_name", "Company")
    st.title(f"{company_name} Chatbot")
    st.write(f"Ask any questions about {company_name}'s documents.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is your question?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                token = st.session_state.get('token')
                if token:
                    # Get a streaming response from the API
                    response_generator = api_client.query_chatbot_stream(token, prompt)

                    # Use st.write_stream to display the response as it arrives
                    assistant_response = st.write_stream(response_generator)

                    # Add the final, full response to the chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

                else:
                    st.error("Authentication error. Please login again.")