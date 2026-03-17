const storageKey = "awesomerag-session-id";

function makeSessionId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `session-${Math.random().toString(36).slice(2, 12)}`;
}

export function getOrCreateSessionId() {
  if (typeof window === "undefined") {
    return "server-render";
  }

  const existingId = window.localStorage.getItem(storageKey);
  if (existingId) {
    return existingId;
  }

  const nextId = makeSessionId();
  window.localStorage.setItem(storageKey, nextId);
  return nextId;
}

export function resetSessionId() {
  const nextId = makeSessionId();
  if (typeof window !== "undefined") {
    window.localStorage.setItem(storageKey, nextId);
  }
  return nextId;
}


export function setSessionId(sessionId: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(storageKey, sessionId);
  }
}
