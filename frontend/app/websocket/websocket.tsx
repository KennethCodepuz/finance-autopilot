import React, { createContext, useContext, useState, useEffect } from "react";

const WebSocketContext = createContext<WebSocket | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
   const [socket, setSocket] = useState<WebSocket | null>(null);

   useEffect(() => {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const customWsUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL;

      let baseWsUrl = customWsUrl;
      if (!baseWsUrl) {
         // Auto-derive WebSocket URL from backend HTTP/HTTPS URL
         baseWsUrl = backendUrl.replace(/^http/, "ws").replace(/\/$/, "");
      } else {
         baseWsUrl = baseWsUrl.replace(/\/$/, "");
      }

      const fullWsEndpoint = `${baseWsUrl}/api/ws/activity`;
      console.log("Connecting WebSocket to:", fullWsEndpoint);

      const ws = new WebSocket(fullWsEndpoint);
      setSocket(ws);

      return () => {
         ws.close();
      };
   }, []);

   return (
      <WebSocketContext.Provider value={socket}>
         {children}
      </WebSocketContext.Provider>
   );
}

export const useWebSocket = () => useContext(WebSocketContext);