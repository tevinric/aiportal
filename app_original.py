
import streamlit as st  
import os  
import requests
import Functions

import config

import base64

import streamlit as st
import base64

from login_ui import login_ui

def configure_page_settings(image_file, page_title, favicon):
    # Set page title and favicon
    st.set_page_config(
        page_title=page_title,
        page_icon=favicon,
        #layout="wide"
    )
    
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

def main():
    if st.session_state.get("authenticated", False):
        
        st.sidebar.image("DNA Navigators.png", width=80)
        st.sidebar.title("TIH AI Portal")  
        st.sidebar.markdown("<span style='color:orange'>Powered by the DNA & GIT</span>", unsafe_allow_html=True)
        st.sidebar.write("Select the AI tool you want to use: \n")
        ai_tool = st.sidebar.selectbox("AI Tools", 
                                    ["None", 
                                        "ChatGPT",
                                        "Document Intelligence",
                                        "Audio analysis", 
                                        "Image Generation"]
                                    )
    
    
    #######################################################################################################################################################################################      
    
        if ai_tool == "ChatGPT":
            with st.sidebar:
                
                gpt_app = st.selectbox(
                    "Choose an AI application",
                    ["None",
                    "ChatGPT", 
                    "Smart Goal Creator"]
                )
            if gpt_app == "ChatGPT":
                import functions.chatgpt.chatgpt as chatgpt  
                chatgpt.chatgpt(client)
            elif gpt_app == "Smart Goal Creator":
                import functions.chatgpt.smart_goal_creator as smart_goal
                smart_goal.smart_goal_creator(client)
            else:
                pass
                
        elif ai_tool == "Document Intelligence":
            
            with st.sidebar:
                
                document_intelligence_app = st.selectbox(
                    "Choose an AI application",
                    ["None",
                    "Data Extraction",
                    "Document Summarization", 
                    "PPT Presentation Creator"]
                )

            if document_intelligence_app == "Data Extraction":
                import functions.document_intelligence.data_extraction as dataextraction
                dataextraction.data_extraction(client)
            
            elif document_intelligence_app == "Document Summarization":
                
                import functions.document_intelligence.doc_summary as docsum
                docsum.doc_summary(client)
                        
            elif document_intelligence_app == "PPT Presentation Creator":
                import functions.document_intelligence.ppt_generator as pptgen
                pptgen.ppt_app()
                
            else:
                pass
                    
        elif ai_tool == "Audio analysis":
            
            with st.sidebar:
                audio_analysis_app = st.selectbox(
                        "Choose an AI audio app",
                        ["None",
                        "Audio Transcription", ]
                    )
                
            if audio_analysis_app == "Audio Transcription":
                import functions.audio_analysis.stt_app as stt_app
                stt_app.speech_to_text(client)
        
        elif ai_tool == "Image Generation":
            import functions.image_generation.image_gen as image_gen
            image_gen.image_generation(client)        
                                     
        else:
            pass
    
    else:
        login_ui()

if __name__ == '__main__':
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    main()