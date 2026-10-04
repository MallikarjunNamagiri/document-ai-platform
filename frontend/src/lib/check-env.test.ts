import { describe, expect, it } from "vitest";
import { assertApiUrlConfigured } from "./check-env";

const onVercel = { VERCEL: "1" };

describe("assertApiUrlConfigured", () => {
  it("fails the Vercel build when NEXT_PUBLIC_API_URL is missing, with instructions", () => {
    expect(() => assertApiUrlConfigured({ ...onVercel })).toThrow(/NEXT_PUBLIC_API_URL[\s\S]*Environment Variables/);
  });

  it("fails when the value is blank", () => {
    expect(() => assertApiUrlConfigured({ ...onVercel, NEXT_PUBLIC_API_URL: "  " })).toThrow(/NEXT_PUBLIC_API_URL/);
  });

  it("fails when the protocol is missing, because the browser would treat it as a relative path", () => {
    expect(() =>
      assertApiUrlConfigured({ ...onVercel, NEXT_PUBLIC_API_URL: "my-api.onrender.com" })
    ).toThrow(/https?:\/\//);
  });

  it("fails when production would point at localhost", () => {
    expect(() =>
      assertApiUrlConfigured({ ...onVercel, NEXT_PUBLIC_API_URL: "http://localhost:8000" })
    ).toThrow(/localhost/);
  });

  it("accepts a real https backend URL", () => {
    expect(() =>
      assertApiUrlConfigured({ ...onVercel, NEXT_PUBLIC_API_URL: "https://my-api.onrender.com" })
    ).not.toThrow();
  });

  it("never blocks local development or CI builds that are not on Vercel", () => {
    expect(() => assertApiUrlConfigured({})).not.toThrow();
    expect(() => assertApiUrlConfigured({ NEXT_PUBLIC_API_URL: "http://localhost:8000" })).not.toThrow();
  });
});
