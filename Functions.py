import os
import config

from dotenv import load_dotenv

if config.app_type == 'local_dev':
    # LOAD FROM .ENV FILES FOR LOCAL DEVELOPMENT

    load_dotenv()
    api_key = os.getenv("api_key")
    endpoint  = os.getenv("endpoint")
    stt_api_key = os.getenv("stt_api_key")
    stt_endpoint = os.getenv("stt_endpoint")
    
else:

    api_key = config.api_key
    endpoint  = config.endpoint
    stt_api_key = config.stt_api_key
    stt_endpoint = config.stt_endpoint


def create_client():
    from openai import AzureOpenAI
    
    # Create the OpenAI object
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-01",)
    
    return client
