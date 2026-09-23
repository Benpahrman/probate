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

    let isMounted = true;
    let ws: WebSocket | null = null;
    let reconnectTimer: any = null;

    function connect() {
      if (!isMounted) return;
      try {
        ws = new WebSocket(targetUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) {
            ws?.close();
            return;
          }
          setIsConnected(true);
          // Initial greeting
          ws?.send(JSON.stringify({ type: 'SUBSCRIBE', channel: 'TELEMETRY' }));
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
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
          if (!isMounted) return;
          setIsConnected(false);
          // Reconnect after 3s
          reconnectTimer = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setIsConnected(false);
        };
      } catch (err) {
        if (!isMounted) return;
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        } else if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            ws?.close();
          };
        }
      }
      wsRef.current = null;
    };
  }, [url]);

  const send = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  };

  return { isConnected, events, send };
}
