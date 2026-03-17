import requests
import json
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv() 

def generate(prompt):

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
                "content": prompt
            }
        ]
    }
    response=requests.post(url,headers=headers,json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]



