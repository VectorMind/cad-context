// SSR (Node standalone) is the only target: the API routes under src/pages/api
// are the regeneration bridge to the Python side, so a static build would drop
// the whole point of the app. Stack and layout conventions follow the
// maintainer's astro-huge-doc (Astro 5 + @astrojs/node + React islands).
import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import react from '@astrojs/react';

export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  integrations: [react()],
  server: { port: 4321 },
  vite: {
    // three.js and the r3f stack are client-only; keeping them out of the SSR
    // graph avoids pulling WebGL code into the Node build.
    ssr: { noExternal: [] },
  },
});
