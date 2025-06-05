# CHATGPT API Documentation

## Baseurl

``` https://tbc.co.za```

## Authentication?? 

## Endpoints

Endpoint:                   <b> POST /chatgpt </b> <br>
Description:                API endpoint for a user query to the Azure OpenAI endpoint <br>
Authentication Required:    No <br>

<br>

### Request Body

```json
{
    "model": "model-name", // Defaults to gpt4o-mini -- data_type: text
    "assistant_type": "assistant_type", // Defaults to General AI -- data_type: text
    "temperature": "temperature", // Sliding scale between 0.0 and 1.0 -> Defaults to 0.7 -- data_type: float
    "files": [], // List of uploaded files that get passed to the models context - Currently supports 'txt', 'pdf', 'doc', 'docx', 'csv', 'jpg', 'jpeg', 'png'-- data_type: file
    "user_message" : "user_message", // The request message from the user
    "coversation history" : [{"role":"system", "content":[{"type":"text","text":""}]},{"role":"user", "content":[{"type":"text","text":""}]}, {"role":"assisstant", "content":[{"type":"text","text":""}]} ]  // List of the last 5 conversation between user and assistant. This is passed in with the new prompt so that the LLM will have context of previously asked questions -- data_type: list 
}
```

### Response Body

```json
{
    "response": "output", // The LLM models response to the input prompt -- data type: text
    "input_tokens": "token_count", // THe number of input tokens processed -- data type: int
    "complettion_tokens" : "token_count", // THe number of completion tokens processed -- data type: int
    "total_token": "total_token_count", // The total number of tokens procesed -- data type: int
    "model_used": "model-name"  // The name of the model that was used for the completion -- data type: text
}
```
