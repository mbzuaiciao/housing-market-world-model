import { defineConfig } from "astro/config";

// Resolve before bundling: import.meta.url in app modules moves in production.
export default defineConfig({
  output: "static",
  vite: {
    define: {
      __RESEARCH_ROOT__: JSON.stringify(new URL("../", import.meta.url).href),
    },
  },
});
