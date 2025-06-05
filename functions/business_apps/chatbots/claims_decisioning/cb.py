import os
import streamlit as st
from langchain_community.callbacks.manager import get_openai_callback
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from datetime import datetime
import logging
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.vectorstores import FAISS
import re

# Resource api credentials in the RG:DNA-AI, Resource:claims-cdcb
from config import CDCB_AZURE_OPENAI_KEY, CDCB_AZURE_OPENAI_ENDPOINT, CDCB_AZURE_OPENAI_EMBEDDING_ENDPOINT, VALID_USERNAME, VALID_PASSWORD

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get credentials from environment variables
VALID_USERNAME = VALID_USERNAME
VALID_PASSWORD = VALID_PASSWORD

# Setup Azure variables
api_key = CDCB_AZURE_OPENAI_KEY
endpoint =  CDCB_AZURE_OPENAI_ENDPOINT
embedding_endpoint = CDCB_AZURE_OPENAI_EMBEDDING_ENDPOINT

# Initialize LLM
llm = AzureChatOpenAI(
    openai_api_version="2024-08-01-preview",
    azure_deployment="gpt-4o-mini",
    azure_endpoint=endpoint,
    api_key=api_key,
    temperature=0.7,
)

# Define the base directory and folder name for vectorstore
base_directory = os.getcwd()
chatbot_folder = "claims_decisioning"
vectorstore_path = os.path.join(base_directory,"vectorstores",chatbot_folder)

def preprocess_query(query: str) -> str:
    """Preprocess the query for better matching."""
    query = query.lower()
    query = ' '.join(query.split())
    query = re.sub(r'[^\w\s]', ' ', query)
    return query

def create_enhanced_retriever(vectorstore: FAISS):
    """Create an enhanced retriever with better search configuration."""
    return vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 3,
            "score_threshold": 0.5,
            "fetch_k": 6
        }
    )

def format_source_documents(source_documents):
    """Format source documents with enhanced metadata."""
    if not source_documents:
        return ""
    
    formatted_sources = "\n\nSources:\n"
    seen_sources = set()
    
    for doc in source_documents:
        source = doc.metadata.get('source', 'Unknown')
        page = doc.metadata.get('page', 'N/A')
        
        source_str = f"- {source}"
        if page != 'N/A':
            source_str += f" (Page {page})"
            
        if source_str not in seen_sources:
            formatted_sources += source_str + "\n"
            seen_sources.add(source_str)
            
    return formatted_sources

def check_credentials(username, password):
    """Verify the provided credentials against environment variables."""
    return username == VALID_USERNAME and password == VALID_PASSWORD

def logout():
    """Clear session state and log out the user."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def show_login():
    """Display the login form in the sidebar."""
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        if check_credentials(username, password):
            st.session_state["app_auth"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.sidebar.error("Incorrect username or password. If you require access to this application, please contact the TIH AI COE Administrator")

def main_app():
    """Main application functionality after successful login."""
    cost = 0
            
    # Set up the conversation aliases
    
    user_name = st.session_state.username
    assistant_name = 'Claims Decisioning Chatbot'
    
    with get_openai_callback() as cb:
        try:
            # Header section
            col1_im, col2_im, col3_im, col4_im, col5_im = st.columns(5)
            with col1_im:
                st.write(' ')
            with col2_im:
                st.write(' ')
            with col3_im:
                st.image(os.path.join(base_directory, 'static', "Telesure-logo.png"), width=150 )
            with col4_im:
                st.write(' ')
            with col5_im:
                st.write(' ')
                
            st.markdown("<h2 style='text-align: center; color: white;'>TIH Claims Decisioning Chatbot</h2>", unsafe_allow_html=True)
            st.write(' ')
            st.markdown("<p style='text-align: center;'>I am your helpful AI Claims Decisioning Chatbot. Ask me any questions about Telesure products or policies.</p>", unsafe_allow_html=True)
            
            st.sidebar.markdown("""
            Please note that the AI can make mistakes when responding.
            
            If you encounter any challenges, please contact the TIH AI Center of Excellence.
            """)
            
            # Add logout button
            if st.sidebar.button("Logout"):
                logout()
            
            # Footer for sidebar
            st.sidebar.markdown('<div style="position: fixed; bottom: 0; width: 100%; padding-bottom: 20px;">', unsafe_allow_html=True)
            st.sidebar.image(os.path.join(base_directory, 'static', 'Telesure-logo.png'), width=100)
            st.sidebar.markdown('Powered by the TIH AI Center of Excellence')
            st.sidebar.markdown('</div>', unsafe_allow_html=True)
            
            # Load FAISS vectorstore
            load_path = vectorstore_path
            embeddings = AzureOpenAIEmbeddings(
                azure_deployment='text-embedding-3-large',
                api_key=api_key,
                azure_endpoint=embedding_endpoint,
                chunk_size=3000
            )
            
            # Load the FAISS index
            if os.path.exists(load_path):
                vectorstore = FAISS.load_local(
                    load_path,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                st.error(f"No vectorstore found at {load_path}. Please ensure the FAISS index has been created and saved.")
                return
            
            # Define the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an AI assistant specifically trained on Claims Decisioning documentation. Your primary function is to provide accurate and helpful information about the claims decisioning process that you were trained on. Adhere to the following guidelines strictly:

                1. Scope of Knowledge:
                - Only provide information related to a claims decisioning process.
                - Do not answer questions that are not insurance related or related to the context base.
                - If asked about competitors, respond with: "I'm sorry, but I don't have information about other insurance companies."

                2. Response Format:
                - Always respond in English.
                - If a question is unclear, ask for clarification before attempting to answer.

                3. Information Accuracy:
                - Only use information from the provided context or your training data.
                - If you don't have enough information to answer a question accurately, say: "I don't have enough information to answer that question accurately. Could you please provide more details or ask about the claims decisioning process?"

                Keep your answers short and to the point and do not be suggestive.
                Do not provide context summaries unless it is requested.
                """),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                ("human", "Here's some context that might be helpful: {context}"),
            ])
        
            # Set up the retriever and chains
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            document_chain = create_stuff_documents_chain(llm, prompt)
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            
            # Initialize chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []
                
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=(os.path.join(base_directory, 'static', 'user.png') if message["role"] == "user" else os.path.join(base_directory, 'static', 'chatbot.png'))):
                    if message["role"] == "user":
                        st.markdown(f"<div class='user-name' style='color: lightblue;'>{user_name}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='user-name' style='color: orange;'>{assistant_name}</div>", unsafe_allow_html=True)
                    st.write(' ')
                    st.markdown(message["content"])
                    
            # Handle new messages
            if prompt := st.chat_input("Ask me something..."):
                processed_prompt = preprocess_query(prompt)
                
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user", avatar=os.path.join(base_directory, 'static', 'user.png')):
                    st.markdown(prompt)
                
                chat_history = [
                    HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
                    for m in st.session_state.messages[:-1]
                ]
                
                # Generate response
                result = retrieval_chain.invoke({
                    "input": processed_prompt,
                    "chat_history": chat_history
                })
                
                full_response = result["answer"]
                
                # Add source documents
                source_docs = result.get("context", [])
                if source_docs:
                    formatted_sources = format_source_documents(source_docs)
                    full_response += formatted_sources
                
                # Display response
                with st.chat_message("assistant", avatar=os.path.join(base_directory, 'static', "chatbot.png")):
                    message_placeholder = st.empty()
                    message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
        except Exception as e:
            logger.error(f"Error in main: {str(e)}")
            st.error("An error occurred. Please try again later.")

def claims_cb():
    """Main function to handle authentication and app flow."""
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Check if user provided details
    if "app_auth" not in st.session_state:
        st.session_state["app_auth"] = False

    # Show login form if not authenticated
    if not st.session_state["app_auth"]:
        show_login()
        # Keep main area empty until authenticated
    else:
        main_app()