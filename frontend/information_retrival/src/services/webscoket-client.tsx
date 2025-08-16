import  { useState, useEffect } from 'react';
import { Toaster, toast } from 'sonner';

interface Publication {
    title: string;
    authors: string[];
    publicationYear: number;
}

export function RealtimeNotificationComponent ()  {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");

    socket.onopen = () => {
      console.log("WebSocket connection established.");
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data.replace(/'/g, '"')); // Replace single quotes for valid JSON

        if (message.event === "new_publication") {
          const pub: Publication = message.data;
          toast.info(`New Publication Found: "${pub.title}" by ${pub.authors[0]}`);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket connection closed.");
      setIsConnected(false);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      socket.close();
    };
  }, []);

  return (
    <div>
      <Toaster richColors position="top-right" />
      <div className="p-4 border rounded-lg">
        <h2 className="font-semibold text-lg">Real-time Status</h2>
        <p>
          WebSocket Connection:
          <span className={isConnected ? "text-green-500 font-bold" : "text-red-500 font-bold"}>
            {isConnected ? " Connected" : " Disconnected"}
          </span>
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Keep this component open. You will receive a notification every 10 seconds when a "new" publication is found by the server.
        </p>
      </div>
    </div>
  );
}

