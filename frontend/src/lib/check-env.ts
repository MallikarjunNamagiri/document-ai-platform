type Env = Record<string, string | undefined>;

/**
 * Called from next.config.ts. NEXT_PUBLIC_* values are inlined at build time, so a missing value on
 * Vercel would otherwise ship a site whose API calls silently 404. Fail the build with instructions instead.
 * Only enforced on Vercel builds (VERCEL=1); local dev and other CI are never blocked.
 */
export function assertApiUrlConfigured(env: Env): void {
  if (env.VERCEL !== "1") return;

  const url = (env.NEXT_PUBLIC_API_URL ?? "").trim();
  const fix =
    "Set it in Vercel -> Project Settings -> Environment Variables (for Production and Preview) " +
    "to your backend's public URL, then redeploy.";

  if (!url) {
    throw new Error(`NEXT_PUBLIC_API_URL is not set, so the app cannot reach the backend. ${fix}`);
  }
  if (!/^https?:\/\//i.test(url)) {
    throw new Error(
      `NEXT_PUBLIC_API_URL ("${url}") must start with https:// (or http://); without it the browser treats it as a relative path. ${fix}`
    );
  }
  if (/\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(url)) {
    throw new Error(`NEXT_PUBLIC_API_URL points at localhost ("${url}"), which does not exist on Vercel. ${fix}`);
  }
}
