export type StreamFact = {
  frame_received: boolean;
  fresh: boolean;
  last_frame_age_s: number | null;
};

export type TrafficState = {
  type: string;
  phase: string;
  remain_s: number;
  total_s: number;
  yellow_s: number;
  flow_per_min: Record<string, number>;
  ws_clients?: { ui: number; device: number };
  green_ns_next?: number;
  green_ew_next?: number;
};

export function connectUi(
  onState: (s: TrafficState) => void,
  onOpen?: () => void,
  onClose?: () => void,
): WebSocket {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}//${location.host}/ws/ui`;
  const ws = new WebSocket(url);
  ws.onopen = () => onOpen?.();
  ws.onclose = () => onClose?.();
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data as string);
      if (data.type === "state") onState(data as TrafficState);
    } catch {
      /* Ignore malformed messages; connection state remains independently visible. */
    }
  };
  return ws;
}
