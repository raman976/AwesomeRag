"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { getOrCreateClientId } from "@/lib/client-id";
import { getOrCreateSessionId, resetSessionId, setSessionId as persistSessionId } from "@/lib/session-id";

type IngestDocument = {
  doc_id: string;
  source_file: string;
  user_id: string;
};

type IngestResponse = {
  message: string;
  user_id: string;
  session_id?: string | null;
  files_processed: number;
  chunks_created: number;
  documents: IngestDocument[];
};

type Source = {
  doc_id: string | null;
  source_file: string | null;
  page: number | null;
};

type QueryResponse = {
  answer: string;
  user_id: string;
  session_id: string;
  sources: Source[];
};

type ChatTurn = {
  id: string;
  question: string;
  answer: string;
  sources: Source[];
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function HomePage() {
  const chatTurnRefs = useRef<Record<string, HTMLElement | null>>({});
  const previousTurnCountRef = useRef(0);

  const [clientId, setClientId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [indexedDocuments, setIndexedDocuments] = useState<IngestDocument[]>([]);
  const [query, setQuery] = useState("What is this document about?");
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [ingestError, setIngestError] = useState("");
  const [queryError, setQueryError] = useState("");

  useEffect(() => {
    setClientId(getOrCreateClientId());
    setSessionId(getOrCreateSessionId());
  }, []);

  useEffect(() => {
    const previousCount = previousTurnCountRef.current;
    const currentCount = chatTurns.length;

    if (currentCount > previousCount) {
      const latestTurn = chatTurns[currentCount - 1];
      const target = chatTurnRefs.current[latestTurn.id];
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    previousTurnCountRef.current = currentCount;
  }, [chatTurns]);

  function ensureClientId() {
    if (clientId) {
      return clientId;
    }

    const nextClientId = getOrCreateClientId();
    setClientId(nextClientId);
    return nextClientId;
  }

  async function resolveSessionIdForAction(resolvedClientId: string) {
    if (sessionId) {
      return sessionId;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/session/new`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": resolvedClientId,
        },
        body: JSON.stringify({ previous_session_id: null }),
      });

      const data = (await response.json()) as { session_id?: string; detail?: string };
      if (!response.ok || !data.session_id) {
        throw new Error(data.detail ?? "Could not initialize a session.");
      }

      persistSessionId(data.session_id);
      setSessionId(data.session_id);
      return data.session_id;
    } catch {
      const fallbackSessionId = resetSessionId();
      persistSessionId(fallbackSessionId);
      setSessionId(fallbackSessionId);
      return fallbackSessionId;
    }
  }

  async function startNewSession() {
    setQueryError("");
    const resolvedClientId = ensureClientId();

    try {
      const response = await fetch(`${apiBaseUrl}/session/new`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": resolvedClientId,
        },
        body: JSON.stringify({ previous_session_id: sessionId || null }),
      });

      const data = (await response.json()) as { session_id?: string; detail?: string };
      if (!response.ok || !data.session_id) {
        throw new Error(data.detail ?? "Could not create a new session.");
      }

      persistSessionId(data.session_id);
      setSessionId(data.session_id);
    } catch (error) {
      const fallbackSessionId = resetSessionId();
      setSessionId(fallbackSessionId);
      const message = error instanceof Error ? error.message : "Could not create a new session.";
      setQueryError(`${message} Using local fallback session id.`);
    }

    setChatTurns([]);
    setQueryResult(null);
    setIndexedDocuments([]);
    setIngestResult(null);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFiles = Array.from(event.target.files ?? []);
    setFiles((previousFiles) => {
      const merged = [...previousFiles, ...nextFiles];
      const dedupedMap = new Map<string, File>();

      merged.forEach((file) => {
        const key = `${file.name}-${file.size}-${file.lastModified}`;
        dedupedMap.set(key, file);
      });

      return Array.from(dedupedMap.values());
    });

    event.target.value = "";
    setIngestError("");
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const resolvedClientId = ensureClientId();
    const resolvedSessionId = await resolveSessionIdForAction(resolvedClientId);

    if (!files.length) {
      setIngestError("Choose at least one PDF before uploading.");
      return;
    }

    setIsUploading(true);
    setIngestError("");

    const body = new FormData();
    files.forEach((file) => {
      body.append("files", file);
    });
    body.append("session_id", resolvedSessionId);

    try {
      const response = await fetch(`${apiBaseUrl}/ingest`, {
        method: "POST",
        headers: {
          "X-User-Id": resolvedClientId,
        },
        body,
      });

      const data = (await response.json()) as IngestResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in data ? data.detail ?? "Upload failed." : "Upload failed.");
      }

      const successData = data as IngestResponse;
      setIngestResult(successData);
      if (successData.session_id) {
        setSessionId(successData.session_id);
        persistSessionId(successData.session_id);
      }
      setIndexedDocuments((previousDocuments) => {
        const merged = [...previousDocuments, ...successData.documents];
        const dedupedMap = new Map<string, IngestDocument>();

        merged.forEach((doc) => {
          dedupedMap.set(doc.doc_id, doc);
        });

        return Array.from(dedupedMap.values());
      });
      setFiles([]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setIngestError(message);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const resolvedClientId = ensureClientId();
    const resolvedSessionId = await resolveSessionIdForAction(resolvedClientId);

    if (isUploading) {
      setQueryError("Please wait for document ingestion to finish before asking a question.");
      return;
    }

    if (!query.trim()) {
      setQueryError("Write a question before asking.");
      return;
    }

    setIsAsking(true);
    setQueryError("");

    try {
      const response = await fetch(`${apiBaseUrl}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": resolvedClientId,
        },
        body: JSON.stringify({ query, k: 4, session_id: ingestResult?.session_id ?? resolvedSessionId }),
      });

      const data = (await response.json()) as QueryResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in data ? data.detail ?? "Query failed." : "Query failed.");
      }

      const successData = data as QueryResponse;
      setQueryResult(successData);
      setSessionId(successData.session_id);
      setChatTurns((previousTurns) => [
        ...previousTurns,
        {
          id: `${successData.session_id}-${previousTurns.length + 1}`,
          question: query,
          answer: successData.answer,
          sources: successData.sources,
        },
      ]);
      setQuery("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Query failed.";
      setQueryError(message);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="shell app-frame">
      <header className="topbar">
        <div>
          <p className="eyebrow">Document-native workspace</p>
          <h1 className="title-compact">Session-first RAG workspace</h1>
        </div>

        <div className="session-ctrl">
          <span className="session-chip">Session: {sessionId || "creating..."}</span>
          <button className="session-button small" type="button" onClick={startNewSession}>
            New session
          </button>
        </div>
      </header>

      <section className="workspace-grid workspace-fixed">
        <form className="panel panel-upload compact" onSubmit={handleUpload}>
          <div className="panel-header">
            <div>
              <p className="panel-kicker"></p>
              <h2>Upload documents</h2>
            </div>
            <span className="panel-state">PDF only</span>
          </div>

          <label className="dropzone">
            <input type="file" accept="application/pdf" multiple onChange={handleFileChange} />
            <span className="dropzone-title">Drop PDFs here or browse from disk</span>
          </label>

          <div className="file-stack">
            {files.length ? (
              files.map((file) => (
                <div className="file-row" key={`${file.name}-${file.size}`}>
                  <span>{file.name}</span>
                  <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
              ))
            ) : (
              <p className="muted-copy">No files selected yet.</p>
            )}
          </div>

          <button className="primary-button" type="submit" disabled={isUploading}>
            {isUploading ? "Uploading and indexing..." : "Ingest documents"}
          </button>

          {ingestError ? <p className="status error">{ingestError}</p> : null}

          {ingestResult ? (
            <div className="result-card">
              <div className="result-topline">
                <strong>Latest upload completed</strong>
                <span>{ingestResult.chunks_created} chunks prepared</span>
              </div>
              <div className="metric-row">
                <div>
                  <span className="metric-label">Files</span>
                  <strong>{ingestResult.files_processed}</strong>
                </div>
                <div>
                  <span className="metric-label">User scope</span>
                  <strong>{ingestResult.user_id}</strong>
                </div>
              </div>
              <div className="source-list compact-list">
                {(indexedDocuments.length ? indexedDocuments : ingestResult.documents).map((doc) => (
                  <div className="source-row" key={doc.doc_id}>
                    <div>
                      <strong>{doc.source_file}</strong>
                      <span>{doc.doc_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </form>

        <form className="panel panel-query tall" onSubmit={handleAsk}>
          <div className="panel-header">
            <div>
              <p className="panel-kicker"></p>
              <h2>Conversation</h2>
            </div>
            <span className="panel-state">Attributed answers</span>
          </div>

          <label className="query-field">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask about your uploaded documents"
              rows={5}
            />
          </label>

          <button className="primary-button secondary-tone" type="submit" disabled={isAsking || isUploading}>
            {isAsking ? "Running retrieval..." : "Ask the workspace"}
          </button>

          {queryError ? <p className="status error">{queryError}</p> : null}

          <div className="answer-card chat-window">
            <div className="answer-header">
              <p>Conversation</p>
              <span>{chatTurns.length ? `${chatTurns.length} turn(s)` : "No conversation yet"}</span>
            </div>

            {chatTurns.length ? (
              <div className="chat-list">
                {chatTurns.map((turn) => (
                  <article
                    className="chat-turn"
                    key={turn.id}
                    ref={(node) => {
                      chatTurnRefs.current[turn.id] = node;
                    }}
                  >
                    <p className="chat-role">You</p>
                    <p className="chat-copy">{turn.question}</p>

                    <p className="chat-role">Assistant</p>
                    <div className="chat-copy markdown-copy">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{turn.answer}</ReactMarkdown>
                    </div>

                    <div className="source-list">
                      {turn.sources.length ? (
                        turn.sources.map((source, index) => (
                          <div className="source-row" key={`${turn.id}-${source.doc_id}-${source.page}-${index}`}>
                            <div>
                              <strong>{source.source_file ?? "Unknown source"}</strong>
                              <span>{source.doc_id ?? "No doc id"}</span>
                            </div>
                            <span>{source.page !== null ? `Page ${source.page}` : "Page unknown"}</span>
                          </div>
                        ))
                      ) : (
                        <p className="muted-copy">No sources were returned for this turn.</p>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="answer-copy">
                Ask your first question to start a conversation.
              </p>
            )}
          </div>
        </form>
      </section>

      <footer className="footer-note">Made with ❤️ by Raman</footer>
    </main>
  );
}
