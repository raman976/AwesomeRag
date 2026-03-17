const storageKey = "awesomerag-client-id";

function makeClientId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `client-${Math.random().toString(36).slice(2, 12)}`;
}

export function getOrCreateClientId() {
  if (typeof window === "undefined") {
    return "server-render";
  }

  const existingId = window.localStorage.getItem(storageKey);
  if (existingId) {
    return existingId;
  }

  const nextId = makeClientId();
  window.localStorage.setItem(storageKey, nextId);
  return nextId;
}
