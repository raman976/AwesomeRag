import argparse
import sys
from pathlib import Path

from qdrant_client.models import Distance,VectorParams
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore


if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Backend.DocHandler.embeddings import generate_embeddings
from Backend.DocHandler.splitter import pdf_split_many


DEFAULT_INPUT_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
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
    ids=[doc.metadata["chunk_id"] for doc in document]
    vector_store.add_documents(document, ids=ids)
    print("doc added successfully")


def build_ingestion_summary(document_chunks, user_id, pdf_paths, session_id=None):
    doc_map={}

    for chunk in document_chunks:
        doc_id=chunk.metadata["doc_id"]
        if doc_id not in doc_map:
            doc_map[doc_id]={
                "doc_id": doc_id,
                "source_file": chunk.metadata.get("source_file"),
                "user_id": user_id,
            }

    return {
        "user_id": user_id,
        "session_id": session_id,
        "files_processed": len(pdf_paths),
        "chunks_created": len(document_chunks),
        "documents": list(doc_map.values()),
    }


def ingest_pdf_paths(pdf_paths, user_id, session_id=None):
    content=pdf_split_many(pdf_paths, user_id=user_id, session_id=session_id)
    add_document_to_store(content)
    return build_ingestion_summary(content, user_id=user_id, pdf_paths=pdf_paths, session_id=session_id)


def collect_pdf_paths(input_path):
    path=Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Input path not found: {path}")

    if path.is_file():
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Only PDF files are supported: {path}")
        return [str(path)]

    pdf_files=sorted(path.rglob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found under: {path}")

    return [str(pdf_path) for pdf_path in pdf_files]


def main():
    parser=argparse.ArgumentParser(description="Ingest one or many PDF documents into Qdrant")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to a PDF file or a folder containing PDF files",
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="User identifier used for metadata partitioning",
    )
    args=parser.parse_args()

    user_id=args.user_id
    print(f"Using user_id: {user_id}")

    pdf_paths=collect_pdf_paths(args.input)
    print(f"Found {len(pdf_paths)} PDF file(s) for ingestion")

    result=ingest_pdf_paths(pdf_paths, user_id=user_id)
    print(f"Prepared {result['chunks_created']} chunks")


if __name__ == "__main__":
    main()
