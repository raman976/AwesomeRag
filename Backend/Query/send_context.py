import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Backend.Query.retrieve import get_similar
from Backend.Query.context_builder import build_docs
from Backend.Models.response import generate

def answer(query, k=4):
    content=get_similar(query,k)
    context=build_docs(content)

    prompt=f"""

    You are a intelligent being you have to be respectful and you will only look into the context or document provided to you you will
    not respond with your own knowledge only use the provided context to explain the question
    also dont make the response very long and also very short it should be of moderate length.

    Context:
    {context}

    Question:
    {query}
        """
    
    answer=generate(prompt)
    return answer


print(answer("who is the prime minister of israel"))
    

