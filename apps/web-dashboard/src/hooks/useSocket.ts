import { useEffect } from "react";
import { getSocket } from "@/lib/websocket";

// Hook generique pour s'abonner a un evenement du socket partage
export function useSocketEvent<T = unknown>(
  event: string,
  handler: (payload: T) => void
) {
  useEffect(() => {
    const socket = getSocket();
    socket.on(event, handler);
    return () => {
      socket.off(event, handler);
    };
  }, [event, handler]);
}
