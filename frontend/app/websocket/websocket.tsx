import React, { createContext, useContext, useState, useEffect } from "react";

const WebSocketContext = createContext<WebSocket | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
   const wsUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL;
   const [socket, setSocket] = useState<WebSocket | null>(null);

   useEffect(() => {
      const ws = new WebSocket(`${wsUrl}/api/ws/activity`);
      setSocket(ws);

      return () => { ws.close(); };
   }, []);

   return (
      <WebSocketContext.Provider value={socket}>
         {children}
      </WebSocketContext.Provider>
   )
}

export const useWebSocket = () => useContext(WebSocketContext);   