from collections import defaultdict, deque
from threading import Lock
import uuid


_MAX_TURNS = 10

# Key: (user_id, session_id) -> deque of turns
_store: dict[tuple[str, str], deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=_MAX_TURNS))
_lock = Lock()


def get_or_create_session_id(session_id: str | None) -> str:
    if session_id and session_id.strip():
        return session_id.strip()
    return str(uuid.uuid4())


def get_session_history(user_id: str, session_id: str) -> list[dict[str, str]]:
    key = (user_id, session_id)
    with _lock:
        return list(_store[key])


def append_session_turn(user_id: str, session_id: str, question: str, answer: str) -> None:
    key = (user_id, session_id)
    with _lock:
        _store[key].append(
            {
                "question": question,
                "answer": answer,
            }
        )


def clear_session_history(user_id: str, session_id: str) -> None:
    key = (user_id, session_id)
    with _lock:
        if key in _store:
            del _store[key]
