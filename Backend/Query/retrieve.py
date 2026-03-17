import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Backend.DB.qdrant import get_vector_store

def get_similar(query,k):
    instance=get_vector_store()
    docs=instance.similarity_search(
        query=query,
        k=k
    )
    return docs 