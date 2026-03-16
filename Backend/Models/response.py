import requests
import json
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv() 

url="https://openrouter.ai/api/v1/chat/completions"
headers={
    "Authorization": os.getenv('api_key'),
    "Content-Type": "application/json"
}

data = {
    "model": "stepfun/step-3.5-flash:free",
    "messages": [
        {
            "role": "user",
            "content": "What is RAG in AI?"
        }
    ]
}


response=requests.post(url,headers=headers,json=data)
result = response.json()
print(result["choices"][0]["message"]["content"])