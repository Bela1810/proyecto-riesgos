import React from 'react';
import { LOG_COLORS } from '../../constants';

interface LogEntryProps {
  time: string;
  level: string;
  message: string;
}

export default function LogEntry({ time, level, message }: LogEntryProps) {
  const color = LOG_COLORS[level] ?? '#9ca3af';

  return (
    <div className="log-entry">
      <span className="log-entry__time">[{time}]</span>{' '}
      <span className="log-entry__level" style={{ color }}>{level}:</span>{' '}
      <span className="log-entry__msg">{message}</span>
    </div>
  );
}