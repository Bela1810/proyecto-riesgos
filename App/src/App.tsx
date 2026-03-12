import { useState } from "react";
import Header from "./components/layout/header";
import { MdCalendarMonth } from "react-icons/md";
import "./index.css";
import Form from "./components/ui/form";
import RegisterConsole from "./components/ui/register_console";

const MOCK_LOGS = [
  { time: '10:00:01', level: 'INFO',    message: 'Iniciando conexión con la base de datos de modelos...' },
  { time: '10:00:04', level: 'SUCCESS', message: 'Conexión establecida exitosamente.' },
  { time: '10:00:35', level: 'INFO',    message: 'Escaneando directorio de entrada: 14 archivos encontrados.' },
  { time: '10:01:02', level: 'PROCESS', message: "Procesando 'CARTERA_RETAIL_V1_202310.csv' (34%)..." },
  { time: '10:02:44', level: 'WARNING', message: 'Registro #4502 omitido debido a valores nulos en PD.' },
  { time: '10:05:12', level: 'ERROR',   message: 'Fallo al escribir reporte temporal en C:\\Windows\\Temp (Acceso Denegado).' },
  { time: '10:05:15', level: 'INFO',    message: 'Reintentando con directorio alternativo...' },
  { time: '10:08:21', level: 'WAITING', message: '... Esperando nuevas instrucciones.' },
];

export function App() {
  const [logs, setLogs] = useState(MOCK_LOGS);

  const handleClearLogs = () => setLogs([]);

  return (
    <div className="app">
      <Header />
      <div className="page-header">
        <div className="page-header_title">
          <h2 className="title">Procesamiento de Datos 📊</h2>
          <p className="subtitle">Configure las rutas de origen y destino para calcular la pérdida esperada basándose en los modelos vigentes</p>
        </div>
        <div className="page-header_last">
          <span className="badge-last-run">
            <MdCalendarMonth size={23} color={"#c0161d"} />
            Última Ejecución: 10-10-2024 12:00 PM
          </span>
        </div>
      </div>
      <main className="main-content">
        <Form />
        <RegisterConsole logs={logs}/>
      </main>
    </div>
  );
}

export default App;
