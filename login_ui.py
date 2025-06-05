import requests
import streamlit as st
from msal import ConfidentialClientApplication
import os
import base64

from config import AAD_CLIENT_ID, AAD_CLIENT_SECRET, AAD_TENANT_ID, REDIRECT_URI


def add_bg_from_local(image_file):
    try:
        # Get the absolute path to the background gif

        bg_path = image_file
        
        if not os.path.exists(bg_path):
            st.error(f"Background file not found at {bg_path}")
            return

        with open(bg_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
    
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/gif;base64,{data}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}
            
            .stApp::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.85);  
                z-index: 0;
            }}
            
            .element-container, .stMarkdown, .stImage {{
                position: relative;
                z-index: 1;
            }}
            
            .custom-button {{
                background-color: #0066cc;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                width: 100%;
                margin: 10px 0;
                transition: background-color 0.3s;
            }}
            
            .custom-button:hover {{
                background-color: #0052a3;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        pass

def initialize_app():
    client_id = AAD_CLIENT_ID
    tenant_id = AAD_TENANT_ID
    client_secret = AAD_CLIENT_SECRET
    authority_url = f"https://login.microsoftonline.com/{tenant_id}"
    return ConfidentialClientApplication(client_id, authority=authority_url, client_credential=client_secret)

def acquire_access_token(app, code, scopes, redirect_uri):
    return app.acquire_token_by_authorization_code(code, scopes=scopes, redirect_uri=redirect_uri)

def fetch_user_data(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    graph_api_endpoint = "https://graph.microsoft.com/v1.0/me"
    response = requests.get(graph_api_endpoint, headers=headers)
    return response.json()

def authentication_process(app):
    scopes = ["User.Read"]
    redirect_uri = REDIRECT_URI
    auth_url = app.get_authorization_request_url(scopes, redirect_uri=redirect_uri)
    
    # Replace link with button
    st.markdown(
        f'''
        <a href="{auth_url}">
            <button class="custom-button">
                Sign in with Microsoft
            </button>
        </a>
        ''',
        unsafe_allow_html=True
    )
    
    if st.query_params.get("code"):
        st.session_state["auth_code"] = st.query_params.get("code")
        token_result = acquire_access_token(app, st.session_state.auth_code, scopes, redirect_uri)
        if "access_token" in token_result:
            user_data = fetch_user_data(token_result["access_token"])
            return user_data
        else:
            st.error("Authentication failed. Please try again.")

def login_ui():
    
    # Add the background GIF
    add_bg_from_local(os.path.join(os.getcwd(), "static", "main_background.gif"))
    
    # Create columns with better proportions
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.write(" ")
    with col2:
        # Add some spacing at the top
        st.markdown("<div style='padding: 2rem;'></div>", unsafe_allow_html=True)
        
        logocol1, logocol2, logocol3 = st.columns(3)
       
        with logocol1:
            st.write(" ")
        with logocol2:
                # Center-aligned logo
                st.markdown(
                    "<div style='text-align: center;'>",
                    unsafe_allow_html=True
                )
                st.image(
                    os.path.join(os.getcwd(), "static", "Telesure-logo.png"),
                    width=300
                )
                st.markdown("</div>", unsafe_allow_html=True)
        with logocol3:
            st.write(" ")
        
        # Styled header
        st.markdown(
            """
            <h1 style='text-align: center; font-size: 22px; color: orange; margin-bottom: 1rem; animation: pulse 2s infinite;'>
            Step into the world of AI through our AI portal.
            </h1>
            <style>
            @keyframes pulse {
            0% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.1);
            }
            100% {
                transform: scale(1);
            }
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(
            """

            <p style='text-align: center; color:white; margin-bottom: 2rem;'>
            Please authenticate using your TIH account to proceed.
            </p>
            """,
            unsafe_allow_html=True
        )

        app = initialize_app()
        user_data = authentication_process(app)
        
        if user_data:
            st.success(f"Welcome, {user_data.get('displayName')}!")
            st.session_state["authenticated"] = True
            st.session_state["display_name"] = user_data.get("displayName")
            st.session_state["user_email"] = user_data.get("mail")
            st.rerun()
    
    
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")        
    st.markdown("<div style='margin-top: auto;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align: center; margin-top: 2rem;'>
            <img src="data:image/png;base64,{}" alt="GAIA Logo" style="width: 105px; margin-bottom: 10px;">
            <p style='font-size: 140%; color: orange;'>
                <b>Powered by GAIA</b>
            </p>
        </div>
        """.format(
            base64.b64encode(open(os.path.join(os.getcwd(), "static", "GAIA6.png"), "rb").read()).decode()
        ),
        unsafe_allow_html=True
    )

# if __name__ == "__main__":
#     login_ui()