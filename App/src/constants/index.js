export const LOG_LEVELS = {
  INFO: 'INFO',
  SUCCESS: 'SUCCESS',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  PROCESS: 'PROCESS',
  WAITING: 'WAITING',
};

export const LOG_COLORS = {
  [LOG_LEVELS.INFO]: '#60a5fa',
  [LOG_LEVELS.SUCCESS]: '#4ade80',
  [LOG_LEVELS.WARNING]: '#facc15',
  [LOG_LEVELS.ERROR]: '#f87171',
  [LOG_LEVELS.PROCESS]: '#a78bfa',
  [LOG_LEVELS.WAITING]: '#6b7280',
};

export const MOCK_LOGS = [
  { time: '10:00:01', level: 'INFO',    message: 'Iniciando conexión con la base de datos de modelos...' },
  { time: '10:00:04', level: 'SUCCESS', message: 'Conexión establecida exitosamente.' },
  { time: '10:00:35', level: 'INFO',    message: 'Escaneando directorio de entrada: 14 archivos encontrados.' },
  { time: '10:01:02', level: 'PROCESS', message: "Procesando 'CARTERA_RETAIL_V1_202310.csv' (34%)..." },
  { time: '10:02:44', level: 'WARNING', message: 'Registro #4502 omitido debido a valores nulos en PD.' },
  { time: '10:05:12', level: 'ERROR',   message: 'Fallo al escribir reporte temporal en C:\\Windows\\Temp (Acceso Denegado).' },
  { time: '10:05:15', level: 'INFO',    message: 'Reintentando con directorio alternativo...' },
  { time: '10:08:21', level: 'WAITING', message: '... Esperando nuevas instrucciones.' },
];