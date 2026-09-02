import { once } from "node:events";
import { preview } from "vite";

export default async function globalSetup() {
  const server = await preview({
    preview: {
      host: "127.0.0.1",
      port: 4321,
      strictPort: true,
    },
  });

  if (!server.httpServer.listening) {
    await once(server.httpServer, "listening");
  }

  return async () => {
    await server.close();
  };
}
