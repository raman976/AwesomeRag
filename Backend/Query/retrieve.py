import sys
from pathlib import Path

from qdrant_client import models

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Backend.DB.qdrant import get_vector_store

def _build_filter(user_id, doc_id=None, session_id=None):
    must_conditions=[
        models.FieldCondition(
            key="metadata.user_id",
            match=models.MatchValue(value=user_id),
        )
    ]

    if session_id:
        must_conditions.append(
            models.FieldCondition(
                key="metadata.session_id",
                match=models.MatchValue(value=session_id),
            )
        )

    if doc_id:
        must_conditions.append(
            models.FieldCondition(
                key="metadata.doc_id",
                match=models.MatchValue(value=doc_id),
            )
        )

    return models.Filter(must=must_conditions)


def _doc_identity(doc):
    metadata=doc.metadata or {}
    return (
        metadata.get("doc_id"),
        metadata.get("source_file"),
        metadata.get("page"),
        doc.page_content,
    )


def _diversify_results(scored_docs, k):
    selected=[]
    selected_keys=set()
    covered_doc_ids=set()

    # First pass: cover as many distinct documents as possible.
    for doc, _score in scored_docs:
        identity=_doc_identity(doc)
        if identity in selected_keys:
            continue

        doc_id=doc.metadata.get("doc_id") if doc.metadata else None
        if doc_id and doc_id not in covered_doc_ids:
            selected.append(doc)
            selected_keys.add(identity)
            covered_doc_ids.add(doc_id)

        if len(selected) >= k:
            return selected[:k]

    # Second pass: fill remaining slots with best leftover chunks.
    for doc, _score in scored_docs:
        identity=_doc_identity(doc)
        if identity in selected_keys:
            continue
        selected.append(doc)
        selected_keys.add(identity)
        if len(selected) >= k:
            break

    return selected[:k]


def get_similar(query,k,user_id,doc_id=None,session_id=None):
    instance=get_vector_store()
    retrieval_filter=_build_filter(user_id=user_id, doc_id=doc_id, session_id=session_id)

    try:
        fetch_k=max(k * 6, 20)
        scored_docs=instance.similarity_search_with_score(
            query=query,
            k=fetch_k,
            filter=retrieval_filter,
        )

        if not scored_docs:
            return []

        return _diversify_results(scored_docs, k)
    except Exception:
        docs=instance.similarity_search(
            query=query,
            k=k,
            filter=retrieval_filter,
        )
        return docs