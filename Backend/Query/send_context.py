import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Backend.Query.retrieve import get_similar
from Backend.Query.context_builder import build_docs
from Backend.Models.response import generate


def build_conversation_context(chat_history):
    if not chat_history:
        return "No prior conversation in this session."

    turns = []
    for turn in chat_history:
        turns.append(f"User: {turn.get('question', '')}")
        turns.append(f"Assistant: {turn.get('answer', '')}")

    return "\n".join(turns)


def build_document_overview(docs):
    doc_names = []
    seen = set()

    for doc in docs:
        source_file = (doc.metadata or {}).get("source_file", "unknown")
        if source_file in seen:
            continue
        seen.add(source_file)
        doc_names.append(source_file)

    if not doc_names:
        return "No document names available."

    return "\n".join(f"- {name}" for name in doc_names)


def build_prompt(query, context, chat_history, docs):
    conversation_context = build_conversation_context(chat_history)
    document_overview = build_document_overview(docs)

    return f"""

    You are an intelligent assistant. Use only the provided document context and session conversation history.
    Be respectful and concise, and do not use outside knowledge.
    If multiple documents are relevant, include each one in your response and mention their names.

    Conversation History:
    {conversation_context}

    Available Documents:
    {document_overview}

    Document Context:
    {context}

    Current Question:
    {query}
        """

def build_sources(docs):
    sources = []
    seen_sources = set()

    for doc in docs:
        source = (
            doc.metadata.get("doc_id"),
            doc.metadata.get("source_file"),
            doc.metadata.get("page"),
        )

        if source in seen_sources:
            continue

        seen_sources.add(source)
        sources.append(
            {
                "doc_id": doc.metadata.get("doc_id"),
                "source_file": doc.metadata.get("source_file"),
                "page": doc.metadata.get("page"),
            }
        )

    return sources


def answer(query, user_id, k=4, doc_id=None, session_id=None):
    content = get_similar(query, k, user_id=user_id, doc_id=doc_id, session_id=session_id)
    context = build_docs(content)

    prompt = build_prompt(query=query, context=context, chat_history=[], docs=content)

    answer = generate(prompt)
    return answer


def answer_with_sources(query, user_id, k=4, doc_id=None, chat_history=None, session_id=None):
    content = get_similar(query, k, user_id=user_id, doc_id=doc_id, session_id=session_id)

    if not content:
        return {
            "answer": "No matching documents were found for this query.",
            "sources": [],
            "user_id": user_id,
        }

    context = build_docs(content)

    prompt = build_prompt(query=query, context=context, chat_history=chat_history or [], docs=content)

    return {
        "answer": generate(prompt),
        "sources": build_sources(content),
        "user_id": user_id,
    }


def main():
    parser=argparse.ArgumentParser(description="Ask questions over local user-scoped documents")
    parser.add_argument("--query", required=True, help="Question to ask")
    parser.add_argument("--user-id", required=True, help="User identifier used for metadata filtering")
    parser.add_argument("--k", type=int, default=4, help="Number of chunks to retrieve")
    parser.add_argument("--doc-id", help="Optional doc_id to narrow search to one document")
    parser.add_argument("--session-id", help="Optional session identifier to scope retrieval")
    args=parser.parse_args()

    print(answer(args.query, user_id=args.user_id, k=args.k, doc_id=args.doc_id, session_id=args.session_id))


if __name__ == "__main__":
    main()
    

