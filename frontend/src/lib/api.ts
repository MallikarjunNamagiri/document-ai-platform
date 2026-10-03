// const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// vercel url config
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

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
  const response = await fetch(`${API_BASE}/api/status`);
  if (!response.ok) {
    throw new Error("Failed to fetch system status");
  }
  return response.json();
}

/**
 * Fetches all available PDF documents in the backend data directory
 */
export async function fetchAvailableDocuments(): Promise<DocumentListResponse> {
  const response = await fetch(`${API_BASE}/api/documents`);
  if (!response.ok) {
    throw new Error("Failed to fetch available documents");
  }
  return response.json();
}

/**
 * Selects and mounts an existing document from backend storage
 */
export async function selectDocument(filename: string): Promise<DocumentActionResponse> {
  const response = await fetch(`${API_BASE}/api/documents/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to select document");
  }
  return response.json();
}

/**
 * Uploads a new PDF document and indexes it into the vector store
 */
export async function uploadDocument(file: File): Promise<DocumentActionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload document");
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
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      document_hash: docHash,
      chat_history: chatHistory,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Error streaming response");
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
  const response = await fetch(`${API_BASE}/api/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, answer, contexts }),
  });
  if (!response.ok) {
    throw new Error("Evaluation request failed");
  }
  return response.json();
}

