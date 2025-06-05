# Using Azure Key Valut to manage your keys and secrets


This method is preferred since it is more secure and you would not need to expose keys or secrets in your environment file. 


### Step 1: 

Ensure that your code has reference to key vault in the code

Example:

import os

from azure.identity import ManagedIdentityCredential  # Managed identity is used to provide the app system access to the key valut - The app will need to be registered with Entra ID to access the key vault
from azure.keyvault.secrets import SecretClient


key_vault_url = "https://dna-ai-keyvault.vault.azure.net/"
credential = ManagedIdentityCredential()
kv_client = SecretClient(vault_url=key_vault_url, credential=credential)  


# Accessing the key vault secrets
api_key = kv_client.get_secret("apikey").value
endpoint  = kv_client.get_secret("endpoint").value



### Step 2: Manage the App identity

- Navigate to the webapp
- Go to the App Settings > Identity 
- Change status to "On" this will require you to create an app registration in Entra ID
- Create a permissions role assignment

### Step 3: Add the app to the key vault

- Navigate to the key vault
- Navigate to setting > Access configurations
- Go create a new access policy (Go to access control (IAM))
- Add a new role assignment
- Search role for "Key Valut Reader"
- Click assign access to " Managed Identity"
- Click "select members"
- Choose Subscription where the APP is 
- Select App Service as the managed identiyu
- Select the app that was created
- Create the connection to give the app access to the key vault







