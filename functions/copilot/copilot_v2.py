import streamlit as st
import requests
import msal
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from openai import AzureOpenAI
import pytz

# Configuration and Settings
st.set_page_config(page_title="Microsoft Graph Chatbot", layout="wide")

from config import (
    AAD_CLIENT_ID, 
    AAD_CLIENT_SECRET, 
    AAD_TENANT_ID,
    api_key,
    endpoint,
)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-02-15-preview",
    azure_endpoint=endpoint
)

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# App config
APP_CONFIG = {
    "client_id": AAD_CLIENT_ID,
    "client_secret": AAD_CLIENT_SECRET,
    "authority": f"https://login.microsoftonline.com/{AAD_TENANT_ID}",
    "scope": ["User.Read", "Mail.Read", "Calendars.Read", "Contacts.Read"],
    "redirect_uri": "http://localhost:8501"
}

def initialize_msal_app():
    return msal.ConfidentialClientApplication(
        APP_CONFIG["client_id"],
        authority=APP_CONFIG["authority"],
        client_credential=APP_CONFIG["client_secret"]
    )

def get_auth_url():
    msal_app = initialize_msal_app()
    return msal_app.get_authorization_request_url(
        scopes=APP_CONFIG["scope"],
        redirect_uri=APP_CONFIG["redirect_uri"]
    )

def get_token_from_code(auth_code):
    msal_app = initialize_msal_app()
    return msal_app.acquire_token_by_authorization_code(
        code=auth_code,
        scopes=APP_CONFIG["scope"],
        redirect_uri=APP_CONFIG["redirect_uri"]
    )

def make_graph_request(endpoint: str, token: str, method: str = "GET", data: Dict = None) -> Dict:
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    url = f'https://graph.microsoft.com/v1.0{endpoint}'
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    
    return response.json()

def find_contact(name: str, token: str) -> Optional[Dict]:
    """
    Enhanced search for a contact using both People API and Contacts API.
    Prioritizes people you interact with most frequently.
    """
    # First try searching in people (includes recent interactions and relevance)
    people_query = f"/me/people?$search='{name}'&$top=5&$select=displayName,emailAddresses,scoredEmailAddresses,personType&$orderby=relevanceScore desc"
    response = make_graph_request(people_query, token)
    
    if "value" in response and response["value"]:
        for person in response["value"]:
            # Check if this is a person (not a distribution list or other type)
            if person.get("personType", {}).get("class") == "Person":
                # Get email address from either scoredEmailAddresses or emailAddresses
                email = None
                if "scoredEmailAddresses" in person and person["scoredEmailAddresses"]:
                    email = person["scoredEmailAddresses"][0].get("address")
                elif "emailAddresses" in person and person["emailAddresses"]:
                    email = person["emailAddresses"][0].get("address")
                
                if email:
                    return {
                        "displayName": person.get("displayName", ""),
                        "emailAddress": email,
                        "source": "people"
                    }
    
    # If not found in people, try fuzzy matching in contacts
    contacts_query = f"/me/contacts?$select=displayName,emailAddresses&$filter=contains(displayName,'{name}') or contains(emailAddresses/any(e:e/address),'{name}')"
    response = make_graph_request(contacts_query, token)
    
    if "value" in response and response["value"]:
        contact = response["value"][0]
        if "emailAddresses" in contact and contact["emailAddresses"]:
            return {
                "displayName": contact.get("displayName", ""),
                "emailAddress": contact["emailAddresses"][0].get("address", ""),
                "source": "contacts"
            }
    
    # If still not found, try searching in directory
    directory_query = f"/users?$filter=startswith(displayName,'{name}') or startswith(mail,'{name}')&$select=displayName,mail"
    response = make_graph_request(directory_query, token)
    
    if "value" in response and response["value"]:
        user = response["value"][0]
        return {
            "displayName": user.get("displayName", ""),
            "emailAddress": user.get("mail", ""),
            "source": "directory"
        }
    
    return None

def get_latest_email_from_person(person_name: str, token: str) -> Dict:
    """Get the latest email from a specific person with enhanced contact search."""
    contact = find_contact(person_name, token)
    if not contact:
        # Try alternative search methods
        # 1. Search in message history
        messages_query = f"/me/messages?$search=\"from:{person_name}\"&$top=1&$orderby=receivedDateTime desc"
        messages = make_graph_request(messages_query, token)
        
        if "value" in messages and messages["value"]:
            message = messages["value"][0]
            return {
                "subject": message["subject"],
                "from": message["from"],
                "receivedDateTime": message["receivedDateTime"],
                "bodyPreview": message["bodyPreview"]
            }
        
        return {"error": f"Could not find any emails from or contact matching: {person_name}"}
    
    # Use the found contact's email to search for messages
    email_address = contact["emailAddress"]
    query = f"/me/messages?$filter=from/emailAddress/address eq '{email_address}'&$orderby=receivedDateTime desc&$top=1"
    response = make_graph_request(query, token)
    
    if "value" in response and response["value"]:
        message = response["value"][0]
        return {
            "subject": message["subject"],
            "from": message["from"],
            "receivedDateTime": message["receivedDateTime"],
            "bodyPreview": message["bodyPreview"],
            "contactInfo": contact
        }
    return {"error": f"No emails found from {contact['displayName']} ({email_address})"}

def find_available_time_slot(person_name: str, token: str) -> Dict:
    """Find the next available time slot with enhanced contact search."""
    contact = find_contact(person_name, token)
    if not contact:
        return {"error": f"Could not find contact: {person_name}. Please try with their full name or email address."}
    
    email_address = contact["emailAddress"]
    
    # Get current user's calendar for the next week
    start_time = datetime.now(pytz.UTC)
    end_time = start_time + timedelta(days=7)
    
    # Format times for Graph API
    start_str = start_time.isoformat()
    end_str = end_time.isoformat()
    
    # Get both users' schedules
    schedules_endpoint = "/users/schedule/getSchedule"
    schedule_data = {
        "schedules": ["me", email_address],
        "startTime": {
            "dateTime": start_str,
            "timeZone": "UTC"
        },
        "endTime": {
            "dateTime": end_str,
            "timeZone": "UTC"
        },
        "availabilityViewInterval": 30
    }
    
    response = make_graph_request(schedules_endpoint, token, method="POST", data=schedule_data)
    
    if "value" in response:
        available_slots = []
        current_time = start_time
        
        while current_time < end_time:
            # Only check during business hours (9 AM to 5 PM)
            local_time = current_time.astimezone(pytz.timezone('UTC'))
            if local_time.hour >= 9 and local_time.hour < 17 and local_time.weekday() < 5:  # Monday to Friday
                is_available = True
                for schedule in response["value"]:
                    availability_view = schedule.get("availabilityView", "")
                    time_index = int((current_time - start_time).total_seconds() / 1800)  # 30-minute slots
                    if time_index < len(availability_view) and availability_view[time_index] != "0":
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(current_time)
            
            current_time += timedelta(minutes=30)
        
        if available_slots:
            return {
                "availableSlot": available_slots[0].isoformat(),
                "duration": "30 minutes",
                "contactInfo": contact
            }
    
    return {
        "error": f"No available time slots found in the next week for {contact['displayName']}"
    }

def process_user_query(query: str, token: str) -> Dict:
    """Process natural language query with improved error handling and debugging."""
    system_message = """You are a helpful assistant that interprets natural language queries about emails and calendar events.
    For each query, respond with a JSON object following this exact format:
    {
        "intent": "<intent_type>",
        "person_name": "<extracted_name>",
        "other_params": {}
    }
    
    Where intent_type must be one of: "latest_email", "available_time", "unknown"
    
    Examples:
    User: "What's the latest email from John Smith?"
    Assistant: {"intent": "latest_email", "person_name": "John Smith", "other_params": {}}
    
    User: "When can I meet with Jane Doe?"
    Assistant: {"intent": "available_time", "person_name": "Jane Doe", "other_params": {}}
    
    User: "Show me emails from john.doe@company.com"
    Assistant: {"intent": "latest_email", "person_name": "john.doe@company.com", "other_params": {}}
    
    Always ensure your response is valid JSON with these exact fields.
    Extract the full name or email address provided in the query."""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt4o",
            messages=messages,
            temperature=0,
            response_format={ "type": "json_object" }
        )
        
        parsed_intent = json.loads(response.choices[0].message.content)
        
        if parsed_intent["intent"] == "latest_email":
            return get_latest_email_from_person(parsed_intent["person_name"], token)
        elif parsed_intent["intent"] == "available_time":
            return find_available_time_slot(parsed_intent["person_name"], token)
        else:
            return {
                "error": "I couldn't understand what you're asking for. Try asking about latest emails or finding available meeting times."
            }
            
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse AI response. Raw response: {response.choices[0].message.content if 'response' in locals() else 'No response'}"
        }
    except Exception as e:
        return {"error": f"Error processing query: {str(e)}"}

# UI Components
st.title("Microsoft Graph Chatbot")

# Authentication Flow
if not st.session_state.access_token:
    st.warning("Please authenticate with Microsoft Graph")
    if st.button("Login"):
        auth_url = get_auth_url()
        st.markdown(f"[Click here to login]({auth_url})")
    
    # Handle authentication code
    auth_code = st.experimental_get_query_params().get("code")
    if auth_code:
        token_response = get_token_from_code(auth_code[0])
        if "access_token" in token_response:
            st.session_state.access_token = token_response["access_token"]
            st.rerun()
        else:
            st.error("Authentication failed!")

# Main Chat Interface
if st.session_state.access_token:
    st.success("✓ Authenticated with Microsoft Graph")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your emails and calendar..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Process query and get response
        response = process_user_query(prompt, st.session_state.access_token)
        
        # Format response for display
        if "error" in response:
            response_text = f"Error: {response['error']}"
        elif "subject" in response:  # Email response
            response_text = f"""
            Subject: {response['subject']}
            From: {response['from']['emailAddress']['address']}
            Received: {response['receivedDateTime']}
            
            {response['bodyPreview']}
            """
        elif "availableSlot" in response:  # Calendar response
            response_text = f"Next available time slot: {response['availableSlot']} ({response['duration']})"
        else:
            response_text = json.dumps(response, indent=2)
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        
        # Rerun to update chat display
        st.rerun()
    
    # Logout option
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.user_info = None
        st.session_state.chat_history = []
        st.rerun()