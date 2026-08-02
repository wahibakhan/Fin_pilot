import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal, self-contained server bundle (server.js + only the
  // node_modules actually used) for the Docker runtime stage — see
  // frontend/Dockerfile, which sets BUILD_STANDALONE=1. Must stay unset for
  // platform builds (Vercel): "standalone" output changes what Next emits
  // in a way that conflicts with how Vercel serves the app, causing a
  // NOT_FOUND on every route.
  output: process.env.BUILD_STANDALONE === "1" ? "standalone" : undefined,
};

export default nextConfig;
