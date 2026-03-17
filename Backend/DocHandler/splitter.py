from langchain_text_splitters import RecursiveCharacterTextSplitter 
from .loader import pdf_loader

def pdf_split(fiile_path):
    splitter=RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",  chunk_size=800,chunk_overlap=150
    )
    texts=splitter.split_documents(documents=pdf_loader(fiile_path))
    return texts
