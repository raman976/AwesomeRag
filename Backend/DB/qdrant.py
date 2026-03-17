import sys
from pathlib import Path

from qdrant_client.models import Distance,VectorParams
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore


if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Backend.DocHandler.embeddings import generate_embeddings
from Backend.DocHandler.splitter import pdf_split


SAMPLE_PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "A_Intro_to_AI_ML_Project_Title_in_IEEE_Double_Column_Format__1_-3.pdf"
)


def get_vector_store():
    client=QdrantClient(
        host="localhost",
        port=6333
    )

    collection_name="master"
    vector_size=len(generate_embeddings().embed_query("test"))

    if not client.collection_exists(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size,distance=Distance.COSINE)
        )
    
    vector_store=QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=generate_embeddings()
    )


    return vector_store 



def add_document_to_store(document):
    vector_store=get_vector_store()
    vector_store.add_documents(document)
    print("doc added successfully")


def main():
    content = pdf_split(str(SAMPLE_PDF_PATH))
    add_document_to_store(content)


if __name__ == "__main__":
    main()
