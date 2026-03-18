import hashlib
import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .loader import pdf_loader


def _create_splitter():
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=800,
        chunk_overlap=150,
    )


def pdf_split(file_path):
    splitter = _create_splitter()
    texts = splitter.split_documents(documents=pdf_loader(file_path))
    return texts


def _normalize_file_spec(file_spec):
    if isinstance(file_spec, str):
        path = Path(file_spec)
        return {
            "path": str(path),
            "source_file": path.name,
            "doc_key": str(path.resolve()),
        }

    if isinstance(file_spec, dict) and file_spec.get("path"):
        path = Path(file_spec["path"])
        return {
            "path": str(path),
            "source_file": file_spec.get("source_file", path.name),
            "doc_key": file_spec.get("doc_key", str(path.resolve())),
        }

    raise ValueError("Invalid file specification")


def _build_doc_id(doc_key):
    return hashlib.sha256(doc_key.encode("utf-8")).hexdigest()[:16]


def _build_chunk_id(user_id, doc_id, page_number, chunk_index, session_id=None):
    scope = session_id or "global"
    raw = f"{user_id}:{scope}:{doc_id}:{page_number}:{chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def pdf_split_many(file_paths, user_id, session_id=None):
    splitter = _create_splitter()
    all_texts = []

    for file_spec in file_paths:
        normalized_file = _normalize_file_spec(file_spec)
        file_path = normalized_file["path"]
        docs = pdf_loader(file_path)
        texts = splitter.split_documents(documents=docs)

        doc_id = _build_doc_id(normalized_file["doc_key"])
        source_file = normalized_file["source_file"]

        for chunk_index, chunk in enumerate(texts):
            page_number = chunk.metadata.get("page")
            chunk_id = _build_chunk_id(user_id, doc_id, page_number, chunk_index, session_id=session_id)
            chunk.metadata["user_id"] = user_id
            if session_id:
                chunk.metadata["session_id"] = session_id
            chunk.metadata["doc_id"] = doc_id
            chunk.metadata["source_file"] = source_file
            chunk.metadata["chunk_id"] = chunk_id

        all_texts.extend(texts)

    return all_texts