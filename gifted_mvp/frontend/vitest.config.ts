import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    // Thread workers start reliably on Windows (the default forks pool timed out here).
    pool: "threads",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
