import { io, Socket } from "socket.io-client";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (socket) return socket;
  // Same origin in prod; Vite proxies /socket.io to Flask in dev.
  socket = io({ autoConnect: true, transports: ["websocket", "polling"] });
  return socket;
}
