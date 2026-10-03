import { afterEach, describe, expect, it, vi } from "vitest";
import { uploadDocument } from "./api";

const pdf = () => new File([new Uint8Array([37, 80, 68, 70])], "contract.pdf", { type: "application/pdf" });

function mockFetch(response: Response) {
  const fn = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("uploadDocument", () => {
  it("posts the file to <API URL>/api/upload and returns the parsed result", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com");
    const fetchMock = mockFetch(
      new Response(JSON.stringify({ name: "contract.pdf", hash: "abc", chunks: 7 }), { status: 200 })
    );

    const result = await uploadDocument(pdf());

    expect(result).toEqual({ name: "contract.pdf", hash: "abc", chunks: 7 });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://backend.example.com/api/upload");
    expect(init.method).toBe("POST");
    expect((init.body as FormData).get("file")).toBeInstanceOf(File);
  });

  it("does not produce a double slash when the API URL has a trailing slash", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com/");
    const fetchMock = mockFetch(new Response(JSON.stringify({ name: "a", hash: "b", chunks: 1 })));

    await uploadDocument(pdf());

    expect(fetchMock.mock.calls[0][0]).toBe("https://backend.example.com/api/upload");
  });

  it("shows the backend's JSON detail message", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com");
    mockFetch(new Response(JSON.stringify({ detail: "Only PDF documents are supported." }), { status: 400 }));

    await expect(uploadDocument(pdf())).rejects.toThrow("Only PDF documents are supported.");
  });

  it("explains a 413 from a proxy that returns a plain-text body", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com");
    mockFetch(new Response("Request Entity Too Large\nFUNCTION_PAYLOAD_TOO_LARGE", { status: 413 }));

    await expect(uploadDocument(pdf())).rejects.toThrow(/too large.*413/i);
  });

  it("surfaces status and body text for non-JSON server errors instead of a generic message", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com");
    mockFetch(new Response("An error occurred with your deployment", { status: 502 }));

    await expect(uploadDocument(pdf())).rejects.toThrow(/502[\s\S]*An error occurred with your deployment/);
  });

  it("tells the developer to set NEXT_PUBLIC_API_URL when the API URL is not configured and the route 404s", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    mockFetch(new Response("<html>404 page</html>", { status: 404 }));

    await expect(uploadDocument(pdf())).rejects.toThrow(/NEXT_PUBLIC_API_URL/);
  });
});
