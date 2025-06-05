import os

app_type = 'dev' # 'prod' 'webapp_prod' 'local_dev'

# ENV VARIABLES

api_key = os.environ.get("AZURE_OPENAI_KEY")
endpoint  = os.environ.get("AZURE_OPENAI_ENDPOINT")
stt_api_key = os.environ.get("AZURE_STT_KEY")
stt_endpoint = os.environ.get("AZURE_STT_ENDPOINT")

# AD DETAILS

AAD_CLIENT_ID = os.environ.get("AAD_CLIENT_ID")
AAD_CLIENT_SECRET = os.environ.get("AAD_CLIENT_SECRET")
AAD_TENANT_ID = os.environ.get("AAD_TENANT_ID")
REDIRECT_URI = os.environ.get("REDIRECT_URI")