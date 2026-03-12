import React, { useEffect, useRef } from 'react';
import "./register_console.css";

export interface LogEntryData {
  time: string;
  level: string;
  message: string;
}

interface RegisterProps {
  logs: LogEntryData[];
}

const LOG_COLORS: Record<string, string> = {
  INFO:    '#60a5fa',
  SUCCESS: '#4ade80',
  WARNING: '#facc15',
  ERROR:   '#f87171',
  PROCESS: '#a78bfa',
  WAITING: '#6b7280',
};

export default function RegisterConsole({ logs}: RegisterProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <section className="card log-card">
      <div className="card-header">
        <span className="card-icon card-icon--red">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="4 17 10 11 4 5" />
            <line x1="12" y1="19" x2="20" y2="19" />
          </svg>
        </span>
        <h2 className="card-title">Registro del Procedimiento</h2>
        <button className="btn-limpiar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14H6L5 6" />
            <path d="M10 11v6M14 11v6" />
            <path d="M9 6V4h6v2" />
          </svg>
          LIMPIAR
        </button>
      </div>

      <div className="log-card-console" role="log" aria-live="polite" aria-label="Registro de ejecución">
        {logs.length === 0 ? (
          <p className="log-card-empty">Sin registros. Ejecute la estimación para ver el progreso.</p>
        ) : (
          logs.map((entry, i) => (
            <div key={i} className="log-entry">
              <span className="log-entry-time">[{entry.time}]</span>{' '}
              <span className="log-entry-level" style={{ color: LOG_COLORS[entry.level] ?? '#9ca3af' }}>
                {entry.level}:
              </span>{' '}
              <span className="log-entry-msg">{entry.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}