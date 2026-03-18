from langchain_community.embeddings import HuggingFaceBgeEmbeddings

_embeddings_cache = None

def generate_embeddings():
    global _embeddings_cache
    if _embeddings_cache is None:
        model_name = "BAAI/bge-small-en" 
        model_kwargs = {"device": "cpu"} 
        encode_kwargs = {"normalize_embeddings": True} 
        _embeddings_cache = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
    return _embeddings_cache


