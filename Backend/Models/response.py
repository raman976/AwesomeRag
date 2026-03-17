import requests
import os
from dotenv import load_dotenv

load_dotenv()


def generate(prompt):
    api_key = os.getenv("api_key")
    if not api_key:
        raise ValueError("Missing 'api_key' in environment variables.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
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

    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    result = response.json()

    if "choices" not in result or not result["choices"]:
        raise ValueError(f"Unexpected model response format: {result}")

    return result["choices"][0]["message"]["content"]



