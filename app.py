import streamlit as st
import os
import base64
from login_ui import login_ui
from typing import Dict, List
from pathlib import Path


import requests
import Functions

import config
from PIL import Image

def configure_page_settings(image_file, page_title, favicon):
    # First initialize session state if not already done
    if "selected_tool" not in st.session_state:
        st.session_state.selected_tool = "None"
    
    # Set page title and favicon
    st.set_page_config(
        page_title=page_title,
        page_icon=favicon,
        layout="wide"  # Set default to wide
    )
    
    # If not on landing page, switch to narrow layout
    if st.session_state.selected_tool != "None":
        st.markdown("""
            <style>
                .main > div {
                    max-width: 1000px;
                    margin: auto;
                    padding-right: 1rem;
                    padding-left: 1rem;
                }
            </style>
        """, unsafe_allow_html=True)
    
    # Add background GIF with dark overlay
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
            .stApp {{
                background-image: url(data:image/gif;base64,{b64_encoded});
                background-size: cover;
                box-shadow: inset 0 0 0 1000px rgba(0,0,0,.85);
            }}
            
            /* Sidebar separator */
            section[data-testid="stSidebar"] {{
                border-right: 2px solid #FF6B00;  /* Orange color */
                box-shadow: 1px 0px 1px #FF6B00;  /* Optional: adds a subtle glow */
            }}
            
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

configure_page_settings(
    image_file='static/main_background.gif',
    page_title='AI Portal',
    favicon='DNA Navigators.png'  # Can be an emoji or path to .ico/.png file
)

app_type = config.app_type

from langchain_community.vectorstores import FAISS                  # --> (U002) For creating the vectorstore of the embeddings (text -> embed to vector -> store in vectorstore)  
from langchain_core.prompts import PromptTemplate        
from langchain_community.callbacks.manager import get_openai_callback
from langchain.chains.question_answering import load_qa_chain
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnablePassthrough

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate


client = Functions.create_client()
  
  
@st.cache_resource
def get_vectorstore(text_content):
    # Create embeddings
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=Functions.endpoint,
        api_key=Functions.api_key,
        api_version="2024-02-01",
        deployment="vectorai3",
    )
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=100,
        length_function=len,
    )
    texts = text_splitter.split_text(text_content)
    
    # Create and return the vectorstore
    return FAISS.from_texts(texts, embeddings)

# Define the base path for images relative to your script
CURRENT_DIR = Path(__file__).parent
IMAGE_DIR = CURRENT_DIR / "static" / "images"

# Create the images directory if it doesn't exist
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Helper function to get absolute image path
def get_image_path(image_name: str) -> Path:
    return IMAGE_DIR / image_name

# Updated APP_METADATA with simplified image paths
APP_METADATA = {
    "chatgpt_general": {
        "name": "ChatGPT",
        "description": "TIH ChatGPT using OpenAI Large Language Models",
        "image_name": "chatgpt.jpg",
        "fallback_emoji": "🤖",
        "category": "Natural Language Processing",
        "sidebar_value": "ChatGPT",
        "parent_app": "ChatGPT",
        "sub_app": "ChatGPT",
        "tags": ["ChatGPT", "Openai", "LLM"],
        "api_available": False
    },
    "chatgpt_smart_goal": {
        "name": "Smart Goal Creator",
        "description": "AI-powered SMART goal creator to help you structure your Workday CPE goals",
        "image_name": "smart_goal_creator.jpg",
        "fallback_emoji": "🎯",
        "category": "Productivity",
        "sidebar_value": "ChatGPT",
        "parent_app": "ChatGPT",
        "sub_app": "Smart Goal Creator",
        "tags": ["Workday", "CPEs", "SMART", "goals", "productivity"],
        "api_available": False
    },
    "doc_extraction": {
        "name": "Data Extraction",
        "description": "Extract data in a structured format from documents using advanced AI processing",
        "image_name": "data_extraction.png",
        "fallback_emoji": "📄",
        "category": "Document Analysis",
        "sidebar_value": "Document Intelligence",
        "parent_app": "Document Intelligence",
        "sub_app": "Data Extraction",
        "tags": ["Data Extraction", "Text mining", "Document Intelligence"],
        "api_available": False
    },
    "doc_summary": {
        "name": "Document Summarization",
        "description": "Use AI to summarise your documents in various summarisation styles",
        "image_name": "document_summarisation.png",
        "fallback_emoji": "📝",
        "category": "Document Analysis",
        "sidebar_value": "Document Intelligence",
        "parent_app": "Document Intelligence",
        "sub_app": "Document Summarization",
        "tags": ["Summarise", "Document Intelligence"],
        "api_available": True
    },
    "ppt_creator": {
        "name": "PPT Presentation Creator",
        "description": "Automatically create professional starter presentations from a prompt or from your documents",
        "image_name": "ppt_creator.png",
        "fallback_emoji": "📊",
        "category": "Document Analysis",
        "sidebar_value": "Document Intelligence",
        "parent_app": "Document Intelligence",
        "sub_app": "PPT Presentation Creator",
        "tags": ["Powerpoint", "Presentation", "PPT"],
        "api_available": False
    },
    "audio_transcription": {
        "name": "Audio Transcription",
        "description": "Convert audio files into text transcriptions that you can ask questions about using advanced AI",
        "image_name": "speech_to_text.png",
        "fallback_emoji": "🎵",
        "category": "Audio Processing",
        "sidebar_value": "Audio analysis",
        "parent_app": "Audio analysis",
        "sub_app": "Audio Transcription",
        "tags": ["Audio", "Transcription", "Speech to text", "Call analysis", "voice", "speaker diarization"],
        "api_available": True
    },
    "image_gen": {
        "name": "Image Generation",
        "description": "Create custom images using advanced AI models",
        "image_name": "image_gen.png",
        "fallback_emoji": "🎨",
        "category": "Computer Vision",
        "sidebar_value": "Image Generation",
        "parent_app": "Image Generation",
        "sub_app": None,
        "tags": ["Images", "Generation", "Dalle", "Content Creation"],
        "api_available": True
    },
    "test_case_generator": {
        "name": "Test Case Generator",
        "description": "Create detailed test scenarios using the power of AI",
        "image_name": "test_case_generator.png",
        "fallback_emoji": "🎵",
        "category": "Natural Language Processing",
        "sidebar_value": "Business Apps",
        "parent_app": "Business Apps",
        "sub_app": "Test Case Generator",
        "tags": ["Testing", "Automation", "Test Cases", "Scenarios"],
        "api_available": True
    },
    "ocr_drivers_license": {
        "name": "OCR - Driver's License",
        "description": "Use OCR to extract data from a driver's license card",
        "image_name": "ocr_drivers.png",
        "fallback_emoji": "🎵",
        "category": "Data Extraction",
        "sidebar_value": "OCR",
        "parent_app": "OCR",
        "sub_app": "Driver's License",
        "tags": ["OCR", "Driver's License", "Data Extraction"],
        "api_available": True
    },
    "ocr_vehicle_license": {
        "name": "OCR - Vehicle License Disc",
        "description": "Use OCR to extract data from a vehicle license disc",
        "image_name": "vehicle_license_disc_ocr.png",
        "fallback_emoji": "🎵",
        "category": "Data Extraction",
        "sidebar_value": "OCR",
        "parent_app": "OCR",
        "sub_app": "Vehicle License Disc",
        "tags": ["OCR", "Vehicle License", "License Disc", "Data Extraction"],
        "api_available": True
    },
    # "ocr_identity_smart_card": {
    #     "name": "OCR - ID Smart Card",
    #     "description": "Use OCR to extract data from a South African ID Smart Card",
    #     "image_name": "vehicle_license_disc_ocr.png",
    #     "fallback_emoji": "🎵",
    #     "category": "Data Extraction",
    #     "sidebar_value": "OCR",
    #     "parent_app": "OCR",
    #     "sub_app": "ID Smart Card",
    #     "tags": ["OCR", "SA ID", "Smart ID", "Data Extraction"],
    #     "api_available": True
    # },
    "claims_decisioning_chatbot": {
        "name": "Claims Decisioning Chatbot",
        "description": "AI Chatbot trained on claims decisioning documentation to assist with claims queries",
        "image_name": "claims_decisioning_chatbot.png",
        "fallback_emoji": "🎵",
        "category": "Chatbot",
        "sidebar_value": "Business Apps",
        "parent_app": "Business Apps",
        "sub_app": "Claims Decisioning Chatbot",
        "tags": ["Claims Decisioning", "Chatbot", "Q&A"],
        "api_available": False
    },
    "comp_anlaysis_chatbot": {
        "name": "Competitor Analysis Chatbot",
        "description": "AI Chatbot trained on competitor assessment documentation",
        "image_name": "competitor_analysis_cb.png",
        "fallback_emoji": "🎵",
        "category": "Chatbot",
        "sidebar_value": "Business Apps",
        "parent_app": "Business Apps",
        "sub_app": "Competitor Analysis Chatbot",
        "tags": ["Competitor Analysis", "Chatbot", "Comparison"],
        "api_available": False
    },
    "text_to_speech": {
    "name": "Text To Speech",
    "description": "Convert text to natural-sounding speech using advanced AI voice technology",
    "image_name": "texttospeech.png",
    "fallback_emoji": "🗣️",
    "category": "Audio Processing",
    "sidebar_value": "Text To Speech",
    "parent_app": "Text To Speech",
    "sub_app": None,
    "tags": ["Audio", "Speech", "Voice", "TTS", "Narration"],
    "api_available": True
    }
}

def load_image(image_name: str) -> Image.Image or None:
    """Load an image from the images directory with error handling"""
    try:
        image_path = get_image_path(image_name)
        if image_path.exists():
            return Image.open(image_path)
        else:
            st.error(f"Image not found: {image_path}")
            return None
    except Exception as e:
        st.error(f"Error loading image {image_name}: {str(e)}")
        return None

def create_app_card(app_id: str, metadata: Dict) -> None:
    with st.container():
        st.markdown("""
            <style>
            .app-card {
                border: 1px solid rgba(255, 107, 0, 0.3);
                border-radius: 10px;
                padding: 12px;
                margin: 10px 5px;
                background-color: rgba(255, 255, 255, 0.05);
                transition: all 0.3s ease;
                height: 100%;
                position: relative;
                box-shadow: 0 0 15px rgba(255, 107, 0, 0.1);
            }
            .app-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 0 20px rgba(255, 107, 0, 0.3);
            }
            .emoji-fallback {
                font-size: 32px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px;
                min-height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .app-title {
                font-size: 1.1em;
                margin: 8px 0;
                font-weight: bold;
            }
            .app-description {
                font-size: 0.85em;
                margin: 6px 0;
                color: rgba(255, 255, 255, 0.8);
            }
            .app-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin-top: 8px;
            }
            .app-tag {
                background-color: rgba(255, 107, 0, 0.2);
                border-radius: 12px;
                padding: 2px 8px;
                font-size: 0.7em;
                color: #FF6B00;
            }
            .api-badge {
                background-color: rgba(0, 255, 0, 0.2);
                color: #00FF00;
                border-radius: 12px;
                padding: 2px 8px;
                font-size: 0.7em;
                display: inline-block;
                margin-top: 4px;
            }
            </style>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        
        # Image/emoji section
        image = load_image(metadata['image_name'])
        if image:
            st.image(image)
        else:
            st.markdown(f"""
                <div class="emoji-fallback">
                    {metadata['fallback_emoji']}
                </div>
                """, unsafe_allow_html=True)
        
        # App details with API badge
        title_row = f"""
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div class='app-title'>{metadata['name']}</div>
                {f"<span class='api-badge'>API Available</span>" if metadata.get('api_available', False) else ""}
            </div>
        """
        st.markdown(title_row, unsafe_allow_html=True)
        
        st.markdown(f"<div class='app-description'>{metadata['description']}</div>", unsafe_allow_html=True)
        
        # Tags
        tags_html = '<div class="app-tags">' + ''.join([f'<span class="app-tag">#{tag}</span>' for tag in metadata['tags']]) + '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
        
        st.markdown(f"<small>**Category:** {metadata['category']}</small>", unsafe_allow_html=True)
        
        if metadata['parent_app'] != metadata['name']:
            st.markdown(f"<small>**Part of:** {metadata['parent_app']}</small>", unsafe_allow_html=True)
        
        if st.button("Launch App", key=f"btn_{app_id}"):
            st.session_state.selected_app = app_id
            st.session_state.selected_tool = metadata['sidebar_value']
            st.session_state.selected_sub_app = metadata['sub_app'] if metadata['sub_app'] else "None"
            st.rerun()
              
        st.markdown('</div>', unsafe_allow_html=True)

def search_apps(query: str, metadata: Dict) -> List[str]:
    """Search through apps and sub-apps based on query"""
    results = []
    query = query.lower()
    
    for app_id, app_data in metadata.items():
        # Include tags in search
        tags_string = ' '.join(app_data['tags']).lower()
        if (query in app_data['name'].lower() or 
            query in app_data['description'].lower() or 
            query in app_data['category'].lower() or
            query in tags_string or
            (app_data['parent_app'] and query in app_data['parent_app'].lower())):
            results.append(app_id)
                
    return results
def render_app_gallery():
    """Render the app gallery home page in a 3x2 grid"""
    
    # DISPLAY TIH LOGO
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: 
        st.write(" ")
    with col2:
        st.write(" ")
    with col3:
        st.image("Telesure-logo.png", width=300)
    with col4:
        st.write(" ")
    with col5:
        st.write(" ")
    
    # DISPLAY LANDING TITLE
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.write(" ")
    with col2:
        st.markdown("""
            <h1 style='text-align: center; color: orange; animation: fadeInOut 3s infinite;'>
             TIH AI PORTAL
            </h1>
            <style>
            @keyframes fadeInOut {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
            }
            </style>
        """, unsafe_allow_html=True)
    with col3:
        st.write(" ")

    st.write(" ")
    st.write(" ")

    # Search and filter controls in single row
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search_query = st.text_input("🔍 Search apps...", key="search_bar")
    with col2:
        categories = sorted(list(set(meta['category'] for meta in APP_METADATA.values())))
        selected_category = st.selectbox("Filter by", ["All Categories"] + categories)
    with col3:
        st.markdown(f"<br>", unsafe_allow_html=True)  # Add spacing
        
    # Filter apps based on search and category
    apps_to_show = list(APP_METADATA.keys())
    if search_query:
        apps_to_show = search_apps(search_query, APP_METADATA)
    if selected_category != "All Categories":
        apps_to_show = [app_id for app_id in apps_to_show 
                       if APP_METADATA[app_id]['category'] == selected_category]
    
    # Show number of results
    st.markdown(f"**{len(apps_to_show)} applications found**")
    
    # Create 3x2 grid layout with more spacing
    # Split apps into rows of 3
    st.markdown("""
        <style>
        .stColumn {
            padding: 0 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create 4-column grid layout
    for i in range(0, len(apps_to_show), 4):
        row_apps = apps_to_show[i:i+4]
        cols = st.columns([1, 1, 1, 1])
        
        # Fill each column with an app card
        for j, app_id in enumerate(row_apps):
            with cols[j]:
                create_app_card(app_id, APP_METADATA[app_id])
        
        # Add spacing between rows
        st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)        
        
def main():
    if st.session_state.get("authenticated", False):
    
    # Initialize all session states first
        if "selected_app" not in st.session_state:
            st.session_state.selected_app = "None"
        if "selected_tool" not in st.session_state:
            st.session_state.selected_tool = "None"
        if "selected_sub_app" not in st.session_state:
            st.session_state.selected_sub_app = "None"
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
            
        # Sidebar
        st.sidebar.image("static/GAIA6.png", width=110)
        st.sidebar.markdown("<span style='color:orange'>Powered by GAIA</span>", unsafe_allow_html=True)
        st.sidebar.title(" AI Portal")
        
        # Add "Back to Gallery" button in sidebar when an app is selected
        if st.session_state.selected_tool != "None":
            if st.sidebar.button("← Back to Gallery"):
                st.session_state.selected_tool = "None"
                st.session_state.selected_app = "None"
                st.session_state.selected_sub_app = "None"
                st.rerun()
            st.sidebar.markdown("---")
        
        
        # Tool selection in sidebar (Test Case Generator should not be here)
        available_tools = ["None", "Business Apps", "ChatGPT", "Document Intelligence", "Audio analysis", "Image Generation", "OCR", "Text To Speech"]
        selected_tool = st.sidebar.selectbox(
            "AI Tools",
            available_tools,
            index=available_tools.index(st.session_state.selected_tool)
        )
                
        # Update selected tool if changed
        if selected_tool != st.session_state.selected_tool:
            st.session_state.selected_tool = selected_tool
            st.session_state.selected_sub_app = "None"
            st.rerun()


        # Main content area
        if st.session_state.selected_tool == "None":
            render_app_gallery()
        else:
            # Handle sub-app selection and rendering based on the selected tool
            if st.session_state.selected_tool == "ChatGPT":
                with st.sidebar:
                    gpt_app = st.selectbox(
                        "Choose an AI application",
                        ["None", "ChatGPT", "Smart Goal Creator"],
                        index=["None", "ChatGPT", "Smart Goal Creator"].index(
                            st.session_state.selected_sub_app)
                    )
                if gpt_app != st.session_state.selected_sub_app:
                    st.session_state.selected_sub_app = gpt_app
                    st.rerun()
                    
                if gpt_app == "ChatGPT":
                    import functions.chatgpt.chatgpt as chatgpt
                    chatgpt.chatgpt(client)
                elif gpt_app == "Smart Goal Creator":
                    import functions.chatgpt.smart_goal_creator as smart_goal
                    smart_goal.smart_goal_creator(client)

            elif st.session_state.selected_tool == "Business Apps":
                with st.sidebar:
                    business_app = st.selectbox(
                        "Choose an AI application",
                        ["None", "Claims Decisioning Chatbot","Competitor Analysis Chatbot" ,"Test Case Generator"],
                        index=["None", "Claims Decisioning Chatbot","Competitor Analysis Chatbot" ,"Test Case Generator"].index(
                            st.session_state.selected_sub_app)
                    )
                if business_app != st.session_state.selected_sub_app:
                    st.session_state.selected_sub_app = business_app
                    st.rerun()
                
                if business_app == "Claims Decisioning Chatbot":
                    import functions.business_apps.chatbots.claims_decisioning.cb as claims_chatbot
                    claims_chatbot.claims_cb()
                              
                elif business_app == "Competitor Analysis Chatbot":
                    import functions.business_apps.chatbots.competitor_analysis.cb as comp_analysis_chatbot
                    comp_analysis_chatbot.comp_analysis_cb()
                       
                elif business_app == "Test Case Generator":
                    import functions.business_apps.test_case_generator as test_case_gen
                    test_case_gen.test_case_generator()
                    

                    
            elif st.session_state.selected_tool == "Document Intelligence":
                with st.sidebar:
                    doc_app = st.selectbox(
                        "Choose an AI application",
                        ["None", "Data Extraction", "Document Summarization", "PPT Presentation Creator"],
                        index=["None", "Data Extraction", "Document Summarization", "PPT Presentation Creator"].index(
                            st.session_state.selected_sub_app)
                    )
                if doc_app != st.session_state.selected_sub_app:
                    st.session_state.selected_sub_app = doc_app
                    st.rerun()
                    
                if doc_app == "Data Extraction":
                    import functions.document_intelligence.data_extraction as dataextraction
                    dataextraction.data_extraction(client)
                elif doc_app == "Document Summarization":
                    import functions.document_intelligence.doc_summary as docsum
                    docsum.doc_summary(client)
                elif doc_app == "PPT Presentation Creator":
                    import functions.document_intelligence.ppt_generator as pptgen
                    pptgen.ppt_app()
                    
            elif st.session_state.selected_tool == "Audio analysis":
                with st.sidebar:
                    audio_app = st.selectbox(
                        "Choose an AI audio app",
                        ["None", "Audio Transcription"],
                        index=["None", "Audio Transcription"].index(
                            st.session_state.selected_sub_app)
                    )
                if audio_app != st.session_state.selected_sub_app:
                    st.session_state.selected_sub_app = audio_app
                    st.rerun()
                    
                if audio_app == "Audio Transcription":
                    import functions.audio_analysis.stt_app as stt_app
                    stt_app.speech_to_text(client)
                    
            elif st.session_state.selected_tool == "Image Generation":
                import functions.image_generation.image_gen as image_gen
                image_gen.image_generation(client)
            
            elif st.session_state.selected_tool == "OCR":
                with st.sidebar:
                    doc_app = st.selectbox(
                        "Choose an AI application",
                        ["None", "Driver's License", "ID Smart Card", "ID Green Book", "Vehicle License Disc"],
                        index=["None", "Driver's License", "ID Smart Card", "ID Green Book", "Vehicle License Disc"].index(
                            st.session_state.selected_sub_app)
                    )
                if doc_app != st.session_state.selected_sub_app:
                    st.session_state.selected_sub_app = doc_app
                    st.rerun()
                    
                if doc_app == "Driver's License":
                    import functions.ocr_apps.drivers_licence as ocr_drivers_license
                    ocr_drivers_license.ocr_drivers_license()
                elif doc_app == "ID Smart Card":
                    import functions.ocr_apps.smart_card_id as smart_card_id
                    smart_card_id.ocr_id_card()
                elif doc_app == "ID Green Book":
                    pass
                elif doc_app == "Vehicle License Disc":
                    import functions.ocr_apps.vehicle_license_disc as vehicle_license_disc
                    vehicle_license_disc.ocr_vehicle_license()

            elif st.session_state.selected_tool == "Text To Speech":
                import functions.tts.tts_app as tts_app
                tts_app.text_to_speech(client)
            
            else:
                pass    
            
    else:
        login_ui()

if __name__ == '__main__':
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    main()
