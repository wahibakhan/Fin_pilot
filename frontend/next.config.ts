import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal, self-contained server bundle (server.js + only the
  // node_modules actually used) for the Docker runtime stage — see
  // frontend/Dockerfile.
  output: "standalone",
};

export default nextConfig;
