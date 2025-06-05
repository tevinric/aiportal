import streamlit as st
import os
from azure.identity import InteractiveBrowserCredential
from msgraph import GraphServiceClient
from openai import AzureOpenAI
import json
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Add these configurations
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")  # Optional, depending on auth type

def initialize_graph_client():
    """Initialize MS Graph client with browser-based authentication"""
    try:
        # Configure the credential with client_id and tenant_id
        credential = InteractiveBrowserCredential(
            client_id=CLIENT_ID,
            tenant_id=TENANT_ID,
            redirect_uri="http://localhost:8501",  # Make sure this matches your Azure AD app registration
            authority=f"https://login.microsoftonline.com/{TENANT_ID}"
        )
        
        # Initialize the Graph client with scopes
        scopes = [
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Calendars.Read',
            'https://graph.microsoft.com/Contacts.Read',
            'https://graph.microsoft.com/Files.Read',
            'https://graph.microsoft.com/User.Read'
        ]
        
        graph_client = GraphServiceClient(
            credentials=credential,
            scopes=scopes
        )
        
        st.session_state.graph_client = graph_client
        return True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        return False

# Add this at the start of your Streamlit app to check authentication status
def check_authentication():
    if not st.session_state.get("authenticated", False):
        st.warning("Please authenticate with Microsoft Graph API")
        if st.button("Login to Microsoft"):
            if initialize_graph_client():
                st.session_state.authenticated = True
                st.success("Successfully authenticated!")
                st.rerun()
        st.stop()



# Configure page
st.set_page_config(page_title="MS Graph Chatbot", page_icon="💬", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph_client" not in st.session_state:
    st.session_state.graph_client = None

# Azure OpenAI Configuration
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# MS Graph API mappings and descriptions
GRAPH_APIS = {
    "list_emails": {
        "description": "List recent emails",
        "keywords": ["emails", "messages", "inbox", "mail"]
    },
    "list_calendar": {
        "description": "List calendar events",
        "keywords": ["calendar", "events", "meetings", "schedule"]
    },
    "list_contacts": {
        "description": "List contacts",
        "keywords": ["contacts", "people", "address book"]
    },
    "list_files": {
        "description": "List OneDrive files",
        "keywords": ["files", "documents", "onedrive"]
    }
}

def initialize_graph_client():
    """Initialize MS Graph client with browser-based authentication"""
    try:
        credential = InteractiveBrowserCredential()
        graph_client = GraphServiceClient(credentials=credential)
        st.session_state.graph_client = graph_client
        return True
    except Exception as e:
        st.error(f"Failed to initialize Graph client: {str(e)}")
        return False

def determine_api_endpoint(question: str) -> tuple:
    """Use Azure OpenAI to determine which Graph API to use based on the question"""
    system_prompt = """You are an AI assistant that helps determine which Microsoft Graph API endpoint to use based on user questions.
    Available APIs and their purposes:
    {api_descriptions}
    
    Respond with a JSON object containing:
    - api_name: the name of the API to use
    - reason: brief explanation of why this API was chosen
    
    If no suitable API is found, respond with {{"api_name": "unknown", "reason": "explanation"}}"""
    
    api_descriptions = "\n".join([f"- {name}: {details['description']}" for name, details in GRAPH_APIS.items()])
    
    messages = [
        {"role": "system", "content": system_prompt.format(api_descriptions=api_descriptions)},
        {"role": "user", "content": question}
    ]
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result["api_name"], result["reason"]

async def execute_graph_query(api_name: str) -> dict:
    """Execute the MS Graph API query using v1.0 endpoints"""
    try:
        client = st.session_state.graph_client
        
        if api_name == "list_emails":
            # Use request configuration
            request = (client.me
                    .messages
                    .get())
            
            # Execute the request and await the response
            response = await request
            
            # Process the response after getting it
            emails = []
            for msg in response.value[:10]:
                email = {
                    "subject": msg.subject,
                    "from": msg.from_property.email_address.address if msg.from_property and msg.from_property.email_address else "Unknown",
                    "receivedDateTime": msg.received_datetime.strftime("%Y-%m-%d %H:%M:%S") if msg.received_datetime else "Unknown"
                }
                emails.append(email)
            
            return {"value": emails}
        
        elif api_name == "list_calendar":
            now = datetime.utcnow().isoformat() + 'Z'
            end_time = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
            
            filter_string = f"start/dateTime ge '{now}' and start/dateTime le '{end_time}'"
            
            request = (client.me
                    .calendar
                    .events
                    .get())
            
            response = await request
            
            events = []
            for event in response.value:
                event_data = {
                    "subject": event.subject,
                    "start": event.start.datetime if event.start else "Unknown",
                    "end": event.end.datetime if event.end else "Unknown"
                }
                events.append(event_data)
            
            return {"value": events}
        
        elif api_name == "list_contacts":
            request = (client.me
                    .contacts
                    .get())
            
            response = await request
            
            contacts = []
            for contact in response.value:
                contact_data = {
                    "name": contact.display_name,
                    "email": contact.email_addresses[0].address if contact.email_addresses else "No email",
                    "phone": contact.business_phones[0] if contact.business_phones else "No phone"
                }
                contacts.append(contact_data)
            
            return {"value": contacts}
        
        elif api_name == "list_files":
            request = (client.me
                    .drive
                    .root
                    .children
                    .get())
            
            response = await request
            
            files = []
            for item in response.value:
                file_data = {
                    "name": item.name,
                    "size": f"{item.size / 1024 / 1024:.2f} MB" if item.size else "Unknown size",
                    "lastModified": item.last_modified_datetime.strftime("%Y-%m-%d %H:%M:%S") if item.last_modified_datetime else "Unknown"
                }
                files.append(file_data)
            
            return {"value": files}
        
        return {"error": "Unknown API endpoint"}
    
    except Exception as e:
        st.error(f"Debug - Error details: {str(e)}")
        return {"error": str(e)}        
    
    
def format_response(api_result: dict, question: str) -> str:
    """Use Azure OpenAI to format the API response in a user-friendly way"""
    system_prompt = """You are an AI assistant that helps format Microsoft Graph API responses into natural language.
    Format the response to directly answer the user's question in a clear and concise way.
    Include only relevant information from the API response."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Question: {question}\nAPI Response: {json.dumps(api_result)}"}
    ]
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content

# Streamlit UI
st.title("MS Graph AI Chatbot")

check_authentication()

# Authentication button
if not st.session_state.graph_client:
    if st.button("Login to Microsoft"):
        if initialize_graph_client():
            st.success("Successfully authenticated!")
            st.rerun()

# Chat interface
if st.session_state.graph_client:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if question := st.chat_input("Ask about your Microsoft data"):
        # Display user message
        with st.chat_message("user"):
            st.write(question)
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Process the question
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Determine which API to use
                api_name, reason = determine_api_endpoint(question)
                
                if api_name == "unknown":
                    response = "I'm sorry, I don't know how to help with that specific question. I can help you with emails, calendar events, contacts, and OneDrive files."
                else:
                    # Execute Graph API query
                    api_result = asyncio.run(execute_graph_query(api_name))
                    
                    if "error" in api_result:
                        response = f"Sorry, I encountered an error: {api_result['error']}"
                    else:
                        # Format the response
                        response = format_response(api_result, question)
                
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# Add some helpful information at the bottom
st.sidebar.markdown("""
## About this chatbot
This chatbot can help you with:
- Checking your emails
- Viewing calendar events
- Managing contacts
- Browsing OneDrive files

Just ask your question naturally, and I'll help you find the information you need!
""")