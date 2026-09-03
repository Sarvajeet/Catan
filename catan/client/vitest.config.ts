import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Unit-test config. Runs in the node environment; component smoke tests use
// react-dom/server (renderToStaticMarkup) so no DOM/jsdom dependency is needed.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
    globals: false,
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
