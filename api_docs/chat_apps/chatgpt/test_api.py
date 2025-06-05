import requests  
import base64  
  
# Replace with your API endpoint URL  
API_URL = 'http://localhost:5000/chatgpt'  
  
def encode_file_to_base64(file_path):  
    with open(file_path, 'rb') as f:  
        return base64.b64encode(f.read()).decode('utf-8')  
  
def create_file_data(file_paths):  
    files_data = []  
    for file_path in file_paths:  
        filename = file_path.split('/')[-1]  # Extract filename from path  
        content_base64 = encode_file_to_base64(file_path)  
        files_data.append({  
            'filename': filename,  
            'content': content_base64  
        })  
    return files_data  
  
def main():  
    # File paths to upload  
    file_paths = [  
        # 'path/to/your/file.txt',          # Text file  
        # 'path/to/your/document.pdf',      # PDF file  
        r"\\GITAGPDSAPR01\Data Sciences\User Space\Priya\Files\Images\Drivers\IMG_6761.jpg",         # Image file  
        # 'path/to/your/spreadsheet.csv',   # CSV file  pip 
        # 'path/to/your/document.docx'      # Word document  
    ]  
  
    # Create files data  
    files_data = create_file_data(file_paths)  
  
    # Prepare the request payload  
    payload = {  
        'model': 'gpt4omini',  # Replace with your deployment ID  
        'assistant_type': 'Technical Assistant',  
        'temperature': '0.7',  
        'files': files_data,  
        'user_message': 'Please analyze the uploaded documents and provide a summary.',  
        'coversation history': [  
            {  
                'role': 'user',  
                'content': [  
                    {  
                        'type': 'text',  
                        'text': 'Hello, I need help with some documents. Please tell me what this image is about'  
                    }  
                ]  
            },  
            # {  
            #     'role': 'assistant',  
            #     'content': [  
            #         {  
            #             'type': 'text',  
            #             'text': 'Sure, please upload the documents, and I will assist you.'  
            #         }  
            #     ]  
            # }  
        ]  
    }  
  
    # Send the POST request  
    response = requests.post(API_URL, json=payload)  
  
    # Check the response  
    if response.status_code == 200:  
        result = response.json()  
        print("Assistant's Response:")  
        print(result['response'])  
        print("\nToken Usage:")  
        print(f"Input Tokens: {result['input_tokens']}")  
        print(f"Completion Tokens: {result['completion_tokens']}")  
        print(f"Total Tokens: {result['total_token']}")  
        print(f"Model Used: {result['model_used']}")  
    else:  
        print(f"Error: {response.status_code}")  
        print(response.text)  
  
if __name__ == '__main__':  
    main()  