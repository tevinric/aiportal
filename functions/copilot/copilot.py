import streamlit as st
import requests
import msal
import json
from datetime import datetime

# Configuration and Settings
st.set_page_config(page_title="Microsoft Graph Explorer", layout="wide")


from config import AAD_CLIENT_ID, AAD_CLIENT_SECRET, AAD_TENANT_ID

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# App config - replace with your values
APP_CONFIG = {
    "client_id": AAD_CLIENT_ID,
    "client_secret": AAD_CLIENT_SECRET,
    "authority": f"https://login.microsoftonline.com/{AAD_TENANT_ID}",
    "scope": ["User.Read", "Mail.Read", "Calendars.Read"],
    "redirect_uri": "http://localhost:8501"  # Default Streamlit port
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
    result = msal_app.acquire_token_by_authorization_code(
        code=auth_code,
        scopes=APP_CONFIG["scope"],
        redirect_uri=APP_CONFIG["redirect_uri"]
    )
    return result

def make_graph_request(endpoint, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f'https://graph.microsoft.com/v1.0{endpoint}', headers=headers)
    return response.json()

# UI Components
st.title("Microsoft Graph Explorer")

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

# Main Application UI (only shown when authenticated)
if st.session_state.access_token:
    st.success("✓ Authenticated with Microsoft Graph")
    
    # Sidebar with available operations
    operation = st.sidebar.selectbox(
        "Select Operation",
        ["Profile Info", "Recent Emails", "Calendar Events", "Custom Query"]
    )
    
    if operation == "Profile Info":
        if st.button("Fetch Profile"):
            profile = make_graph_request("/me", st.session_state.access_token)
            st.json(profile)
    
    elif operation == "Recent Emails":
        if st.button("Fetch Recent Emails"):
            emails = make_graph_request("/me/messages?$top=10", st.session_state.access_token)
            if "value" in emails:
                for email in emails["value"]:
                    with st.expander(f"📧 {email['subject']}"):
                        st.write(f"From: {email['from']['emailAddress']['address']}")
                        st.write(f"Received: {email['receivedDateTime']}")
                        st.write("Body:", email['bodyPreview'])
    
    elif operation == "Calendar Events":
        start_date = st.date_input("Start Date", datetime.now())
        if st.button("Fetch Calendar Events"):
            events = make_graph_request(
                f"/me/calendar/events?$filter=start/dateTime ge '{start_date.isoformat()}'",
                st.session_state.access_token
            )
            if "value" in events:
                for event in events["value"]:
                    with st.expander(f"📅 {event['subject']}"):
                        st.write(f"Start: {event['start']['dateTime']}")
                        st.write(f"End: {event['end']['dateTime']}")
                        st.write(f"Location: {event.get('location', {}).get('displayName', 'No location')}")
    
    elif operation == "Custom Query":
        endpoint = st.text_input("Enter Graph API Endpoint (starting with /)", "/me")
        if st.button("Execute Query"):
            result = make_graph_request(endpoint, st.session_state.access_token)
            st.json(result)
    
    # Logout option
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.user_info = None
        st.rerun()