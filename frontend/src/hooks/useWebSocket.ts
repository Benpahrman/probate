import { useState, useEffect, useRef } from 'react';
import { TelemetryEvent } from '../types';

export function useWebSocket(url?: string) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const defaultUrl = `${protocol}//${host}/api/v1/ws/telemetry`;
    const targetUrl = url || defaultUrl;

    let ws: WebSocket;
    let reconnectTimer: any;

    function connect() {
      try {
        ws = new WebSocket(targetUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          // Initial greeting
          ws.send(JSON.stringify({ type: 'SUBSCRIBE', channel: 'TELEMETRY' }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setEvents((prev) => [data, ...prev].slice(0, 50));
          } catch {
            // raw text event
            setEvents((prev) => [
              {
                type: 'RAW_TELEMETRY',
                message: event.data,
                timestamp: Date.now() / 1000,
              },
              ...prev,
            ].slice(0, 50));
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Reconnect after 3s
          reconnectTimer = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setIsConnected(false);
          ws.close();
        };
      } catch (err) {
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url]);

  const send = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  };

  return { isConnected, events, send };
}
