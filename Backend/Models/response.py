import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


MODEL_NAME = "moonshotai/kimi-k2-instruct-0905"


def generate(prompt):
    api_key = os.getenv("rag_api")
    if not api_key:
        raise ValueError("Missing 'rag_api' in environment variables.")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=1,
        stream=True,
        stop=None,
    )

    chunks = []
    for chunk in completion:
        chunk_text = chunk.choices[0].delta.content or ""
        if chunk_text:
            chunks.append(chunk_text)

    answer = "".join(chunks).strip()
    if not answer:
        raise ValueError("Empty response received from Groq model.")

    return answer



