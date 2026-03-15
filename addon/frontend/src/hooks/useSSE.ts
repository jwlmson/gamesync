import { useState, useEffect, useRef } from 'react';
import { getEventsStreamUrl } from '../api/client';

export interface SSEEvent {
  id: string;
  event_type: string;
  team_id?: string;
  game_id?: string;
  league?: string;
  timestamp: string;
  details?: any;
}

export function useSSE() {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource(getEventsStreamUrl());
    esRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as SSEEvent;
        setEvents((prev) => [event, ...prev].slice(0, 100));
      } catch {
        // Ignore parse errors
      }
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, []);

  return { events, connected };
}
