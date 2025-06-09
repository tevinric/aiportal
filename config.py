import os

app_type = 'dev' # 'prod' 'webapp_prod' 'local_dev'

# OPENAI CREDENTIALS
## General 
api_key = os.environ.get("AZURE_OPENAI_KEY")
endpoint  = os.environ.get("AZURE_OPENAI_ENDPOINT")
embedding_endpoint = os.environ.get("AZURE_OPENAI_EMBEDDING_ENDPOINT")

## Claims Decisioing Chatbot (These credentials are used for the Claims Decisioning Chatbot)
CDCB_AZURE_OPENAI_KEY = os.environ.get("CDCB_AZURE_OPENAI_KEY")
CDCB_AZURE_OPENAI_ENDPOINT = os.environ.get("CDCB_AZURE_OPENAI_ENDPOINT")
CDCB_AZURE_OPENAI_EMBEDDING_ENDPOINT = os.environ.get("CDCB_AZURE_OPENAI_EMBEDDING_ENDPOINT")
VALID_USERNAME = os.environ.get("CLAIMS_CHATBOT_USERNAME")
VALID_PASSWORD = os.environ.get("CLAIMS_CHATBOT_PASSWORD")

## Comppetitor Analysis Chatbot (These credentials are used for the Competitor Analysis Chatbot)
CACB_AZURE_OPENAI_KEY = os.environ.get("CACB_AZURE_OPENAI_KEY")
CACB_AZURE_OPENAI_ENDPOINT = os.environ.get("CACB_AZURE_OPENAI_ENDPOINT")
CACB_AZURE_OPENAI_EMBEDDING_ENDPOINT = os.environ.get("CACB_AZURE_OPENAI_EMBEDDING_ENDPOINT")
CACB_USERNAME= os.environ.get("CACB_USERNAME")
CACB_PASSWORD= os.environ.get("CACB_PASSWORD")

# SPEECH TO TEXT CONNECTION DETAILS
stt_api_key = os.environ.get("AZURE_STT_KEY")
stt_endpoint = os.environ.get("AZURE_STT_ENDPOINT")
tts_key = os.environ.get("AZURE_TTS_KEY")

# AD DETAILS
AAD_CLIENT_ID = os.environ.get("AAD_CLIENT_ID")
AAD_CLIENT_SECRET = os.environ.get("AAD_CLIENT_SECRET")
AAD_TENANT_ID = os.environ.get("AAD_TENANT_ID")
REDIRECT_URI = os.environ.get("REDIRECT_URI")

# SQL SERVER DETAILS
SQL_SERVER = os.environ.get("SQL_SERVER")
SQL_DATABASE = os.environ.get("SQL_DATABASE")
SQL_USERNAME = os.environ.get("SQL_USERNAME")
SQL_PASSWORD = os.environ.get("SQL_PASSWORD")
