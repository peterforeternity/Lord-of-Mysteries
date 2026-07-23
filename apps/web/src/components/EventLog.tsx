import { useRef, useEffect } from "react";
import type { EventLogEntry } from "../types";

interface Props {
  entries: EventLogEntry[];
}

function entryClass(eventType: string): string {
  switch (eventType) {
    case "info":
      return "log-entry-info";
    case "discovery":
      return "log-entry-discovery";
    case "dialogue":
      return "log-entry-dialogue";
    case "ritual":
      return "log-entry-ritual";
    case "combat":
      return "log-entry-combat";
    case "system":
      return "log-entry-system";
    default:
      return "log-entry-info";
  }
}

export default function EventLog({ entries }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  return (
    <div className="card mb-4 max-h-80 overflow-y-auto">
      <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
        事件记录
      </h3>
      {entries.length === 0 ? (
        <p className="text-mystic-text-dim text-xs italic">暂无事件记录</p>
      ) : (
        <div className="space-y-1">
          {entries.map((entry) => (
            <div key={entry.event_id} className={entryClass(entry.event_type)}>
              <div className="flex items-start gap-2">
                <span className="text-mystic-text-dim text-[10px] shrink-0 mt-0.5">
                  {new Date(entry.timestamp).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                <span className="text-xs">{entry.description}</span>
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
