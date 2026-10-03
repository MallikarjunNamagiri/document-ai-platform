/**
 * Backend base URL. Set NEXT_PUBLIC_API_URL in Vercel (Project Settings -> Environment Variables)
 * or in frontend/.env.local for local dev. It is inlined at build time, so redeploy after changing it.
 * Read at call time (not module load) and normalised to have no trailing slash.
 */
function apiBase(): string {
  return (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
}

/**
 * Builds a human-readable message from a failed response. FastAPI sends {"detail": "..."};
 * proxies/platforms (Vercel, Render) send plain text or HTML, which must not be swallowed.
 */
async function readError(response: Response, fallback: string): Promise<string> {
  const raw = await response.text().catch(() => "");
  try {
    const detail = JSON.parse(raw)?.detail;
    if (typeof detail === "string" && detail) return detail;
  } catch {
    // not JSON - fall through
  }
  if (response.status === 413) {
    return "The file is too large for the server (HTTP 413).";
  }
  if (response.status === 404 && !apiBase()) {
    return "API URL is not configured. Set NEXT_PUBLIC_API_URL in your Vercel project's Environment Variables and redeploy (HTTP 404).";
  }
  const body = raw.trim().slice(0, 200);
  return body ? `${fallback} (HTTP ${response.status}): ${body}` : `${fallback} (HTTP ${response.status})`;
}

export interface SystemStatus {
  llm_provider: string;
  llm_connected: boolean;
  model: string;
  vector_db: string;
  vector_status: string;
  retrieval: string;
  guardrail: string;
  semantic_cache_count: string;
  match_threshold: string;
}

export interface DocumentListResponse {
  files: string[];
  active_document: string | null;
}

export interface DocumentActionResponse {
  name: string;
  hash: string;
  chunks: number;
}

export interface RagasMetrics {
  faithfulness: number;
  context_relevancy: number;
  answer_correctness: number;
  status: string;
}

/**
 * Retrieves the live engine and runtime telemetry status
 */
export async function fetchSystemStatus(): Promise<SystemStatus> {
  const response = await fetch(`${apiBase()}/api/status`);
  if (!response.ok) {
    throw new Error("Failed to fetch system status");
  }
  return response.json();
}

/**
 * Fetches all available PDF documents in the backend data directory
 */
export async function fetchAvailableDocuments(): Promise<DocumentListResponse> {
  const response = await fetch(`${apiBase()}/api/documents`);
  if (!response.ok) {
    throw new Error("Failed to fetch available documents");
  }
  return response.json();
}

/**
 * Selects and mounts an existing document from backend storage
 */
export async function selectDocument(filename: string): Promise<DocumentActionResponse> {
  const response = await fetch(`${apiBase()}/api/documents/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  if (!response.ok) {
    throw new Error(await readError(response, "Failed to select document"));
  }
  return response.json();
}

/**
 * Uploads a new PDF document and indexes it into the vector store
 */
export async function uploadDocument(file: File): Promise<DocumentActionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBase()}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Failed to upload document"));
  }

  return response.json();
}

/**
 * Streams tokens and metadata via Server-Sent Events (SSE)
 */
export async function streamChatResponse(
  question: string,
  docHash: string,
  chatHistory: any[],
  onToken: (token: string) => void,
  onComplete: (metadata: any) => void
) {
  const response = await fetch(`${apiBase()}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      document_hash: docHash,
      chat_history: chatHistory,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Error streaming response"));
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) return;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const raw = line.replace("data: ", "").trim();
        if (raw === "[DONE]") return;
        try {
          const payload = JSON.parse(raw);
          if (payload.type === "token") onToken(payload.content);
          if (payload.type === "meta") onComplete(payload);
        } catch {
          // Ignore stream chunk splitting boundaries
        }
      }
    }
  }
}

export async function evaluateTurn(
  question: string,
  answer: string,
  contexts: string[]
): Promise<RagasMetrics> {
  const response = await fetch(`${apiBase()}/api/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, answer, contexts }),
  });
  if (!response.ok) {
    throw new Error("Evaluation request failed");
  }
  return response.json();
}

