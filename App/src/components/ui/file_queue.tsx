import { useState, useEffect } from "react";
import "./file_queue.css";
import { LogEntryData } from "./register_console";

export default function FileQueue({ logs }: { logs: LogEntryData[] }) {
  const [lastMessage, setLastMessage] = useState<LogEntryData | null>(null);
  useEffect(() => {
    if (logs.length > 0) {
      //update the text with last success or error log message
      const lastLog = logs[logs.length - 1];
      if (lastLog?.level === "SUCCESS" || lastLog?.level === "ERROR") {
        setLastMessage(lastLog);
      }
    }
  }, [logs]);
  return (
    <div className="cola-card">
      {logs.length === 0 ? (
        <div className="nothing-label">Aun no hay resultados</div>
      ) : (
        <div
          className={`${lastMessage?.level === "SUCCESS" ? "success-label" : "error-label"}`}
        >
          {lastMessage?.message}
        </div>
      )}
    </div>
  );
}
