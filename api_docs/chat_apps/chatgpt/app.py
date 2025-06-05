from flask import Flask, request, jsonify  
from flask_cors import CORS  
import io  
import threading  
import docx  
import pandas as pd  
from PIL import Image  
import pytesseract  
import fitz  # pymupdf    
from openai import AzureOpenAI
import base64  
import os
from dotenv import load_dotenv

load_dotenv()
  
app = Flask(__name__)  
CORS(app)  
  
# Set up the Azure OpenAI client  
client = AzureOpenAI(
    azure_endpoint=os.getenv("OPENAI_API_ENDPOINT"),
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version="2024-02-01",
)
  
# Allowed file extensions  
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'csv', 'jpg', 'jpeg', 'png'}  
  
# Assistant types mapped to system prompts  
ASSISTANT_TYPES = {  
    'General AI': "You are a helpful AI assistant.",  
    'Technical Assistant': "You are an AI assistant specialized in technical subjects.",  
    'Friendly Assistant': "You are a friendly and engaging AI assistant.",  
    # Add more assistant types and their system prompts as needed  
}  
  
def allowed_file(filename):  
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS  
  
def extract_text_from_file(file_bytes_io, filename):  
    ext = filename.rsplit('.', 1)[1].lower()  
    if ext == 'txt':  
        return file_bytes_io.read().decode('utf-8')  
    elif ext == 'pdf':  
        try:  
            # Use pymupdf to read PDF  
            doc = fitz.open(stream=file_bytes_io.read(), filetype='pdf')  
            text = ''  
            for page in doc:  
                text += page.get_text()  
            return text  
        except Exception as e:  
            print(f"Error reading PDF file {filename}: {e}")  
            return ''  
    elif ext in ['doc', 'docx']:  
        try:  
            doc = docx.Document(file_bytes_io)  
            fullText = []  
            for para in doc.paragraphs:  
                fullText.append(para.text)  
            return '\n'.join(fullText)  
        except Exception as e:  
            print(f"Error reading Word file {filename}: {e}")  
            return ''  
    elif ext == 'csv':  
        try:  
            df = pd.read_csv(file_bytes_io)  
            return df.to_string()  
        except Exception as e:  
            print(f"Error reading CSV file {filename}: {e}")  
            return ''  
    elif ext in ['jpg', 'jpeg', 'png']:  
        try:  
            image = Image.open(file_bytes_io)  
            text = pytesseract.image_to_string(image)  
            return text  
        except Exception as e:  
            print(f"Error reading image file {filename}: {e}")  
            return ''  
    else:  
        return ''  
  
@app.route('/chatgpt', methods=['POST'])  
def chatgpt():  
    data = request.get_json()  
    # Set defaults  
    model = data.get('model', 'gpt4omini')  
    deployment_id = model  # Assuming model name corresponds to deployment name in Azure  
    assistant_type = data.get('assistant_type', 'General AI')  
    temperature = float(data.get('temperature', 0.7))  
    user_message = data.get('user_message', '')  
    conversation_history = data.get('coversation history', [])  
    files_data = data.get('files', [])  
  
    # Build the system prompt  
    system_prompt = ASSISTANT_TYPES.get(assistant_type, ASSISTANT_TYPES['General AI'])  
  
    # Start building the messages list  
    messages = [{'role': 'system', 'content': system_prompt}]  
  
    # Include conversation history  
    for msg in conversation_history:  
        role = msg.get('role')  
        content_list = msg.get('content', [])  
        # Concatenate text content from content_list  
        content_text = ''  
        for content in content_list:  
            if content.get('type') == 'text':  
                content_text += content.get('text', '')  
        messages.append({'role': role, 'content': content_text})  
  
    # Handle uploaded files  
    files_content = ''  
    for file_info in files_data:  
        filename = file_info.get('filename')  
        file_content_base64 = file_info.get('content', '')  
        if allowed_file(filename):  
            try:  
                # Decode base64 content to bytes  
                file_bytes = base64.b64decode(file_content_base64)  
                file_bytes_io = io.BytesIO(file_bytes)  
                text = extract_text_from_file(file_bytes_io, filename)  
                files_content += f'\nContent from {filename}:\n{text}\n'  
            except Exception as e:  
                print(f"Error processing file {filename}: {e}")  
                continue  
        else:  
            print(f"File extension not allowed for file {filename}")  
            continue  
  
    # Append the files content to the user message  
    if files_content:  
        user_message += f'\n{files_content}'  
  
    # Append the user's new message  
    messages.append({'role': 'user', 'content': user_message})  
  
    # Prepare the API call parameters  
    try:  
        # Make the API call using Azure OpenAI client  
        response = client.chat.completions.create(  
            model=deployment_id,  
            messages=messages,  
            temperature=temperature,  
        )  
        
    
  
        # Extract the assistant's reply  
        assistant_reply = response.choices[0].message.content  
  
        # Token usage  
        usage = response.usage  
        input_tokens = usage.prompt_tokens  
        completion_tokens = usage.completion_tokens  
        total_tokens = usage.total_tokens  
  
        # Return the response  
        return jsonify({  
            'response': assistant_reply,  
            'input_tokens': input_tokens,  
            'completion_tokens': completion_tokens,  
            'total_token': total_tokens,  
            'model_used': model  
        })  
  
    except Exception as e:  
        return jsonify({'error': str(e)}), 500  
  
if __name__ == '__main__':  
    # Run the app with threading enabled to handle multiple simultaneous requests  
    app.run(host='0.0.0.0', port=5000, threaded=True)  