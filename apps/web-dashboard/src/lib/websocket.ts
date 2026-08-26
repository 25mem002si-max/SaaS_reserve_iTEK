import { io, Socket } from "socket.io-client";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "http://localhost:8000/";

let socket: Socket | null = null;

// Connexion WebSocket unique et partagee (widget de chat + mises a jour du
// plan de salle en temps reel), fournie par le backend du Developpeur 2.
export function getSocket(): Socket {
  if (!socket) {
    socket = io(WS_URL, {
      transports: ["websocket"],
      autoConnect: true,
    });
  }
  return socket;
}
