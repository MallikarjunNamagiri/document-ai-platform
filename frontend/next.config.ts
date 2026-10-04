import type { NextConfig } from "next";
import { assertApiUrlConfigured } from "./src/lib/check-env";

// Fails the Vercel build early (with instructions) if the backend URL is missing or malformed.
assertApiUrlConfigured(process.env);

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
