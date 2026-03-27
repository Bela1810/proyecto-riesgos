import React, { useState } from "react";
import "./EstimationRunner.css";


const ipcRenderer = (window as any).require
  ? (window as any).require("electron").ipcRenderer
  : null;

export function EstimationRunner() {
  const [inputFolder, setInputFolder] = useState("");
  const [outputFolder, setOutputFolder] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectFolder = async (
    setter: React.Dispatch<React.SetStateAction<string>>,
  ) => {
    if (!ipcRenderer) {
      alert(
        "La selección de carpetas solo está disponible en la aplicación de escritorio.",
      );
      return;
    }
    try {
      const result = await ipcRenderer.invoke("select-folder");
      if (result) {
        setter(result);
      }
    } catch (error) {
      console.error("Error al seleccionar la carpeta:", error);
      setLogs((prev) => [...prev, `Error al seleccionar carpeta: ${error}`]);
    }
  };

  const handleRunEstimation = async () => {
    if (!inputFolder || !outputFolder) {
      alert("Por favor, seleccione las carpetas de entrada y salida.");
      return;
    }

    setIsLoading(true);
    setLogs(["Iniciando estimación..."]);

    try {
      const response = await fetch("http://localhost:5000/api/run-estimation", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          input_folder: inputFolder,
          output_folder: outputFolder,
        }),
      });

      const result = await response.json();

      if (result.status === "success") {
        setLogs((prev) => [
          ...prev,
          "¡Proceso completado con éxito!",
          `Archivos guardados en: ${outputFolder}`,
        ]);
      } else {
        setLogs((prev) => [...prev, `Error en el proceso: ${result.message}`]);
      }
    } catch (error) {
      console.error("Error al ejecutar la estimación:", error);
      setLogs((prev) => [
        ...prev,
        `Error de conexión con el backend: ${error}`,
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="estimation-runner">
      <h2>Estimador de Pérdida Esperada</h2>
      <div className="folder-selector">
        <label>Carpeta de Entrada:</label>
        <input
          type="text"
          value={inputFolder}
          readOnly
          placeholder="Seleccione una carpeta..."
        />
        <button onClick={() => handleSelectFolder(setInputFolder)}>
          Buscar
        </button>
      </div>
      <div className="folder-selector">
        <label>Carpeta de Salida:</label>
        <input
          type="text"
          value={outputFolder}
          readOnly
          placeholder="Seleccione una carpeta..."
        />
        <button onClick={() => handleSelectFolder(setOutputFolder)}>
          Buscar
        </button>
      </div>
      <button
        onClick={handleRunEstimation}
        disabled={isLoading}
        className="run-button">
        {isLoading ? "Procesando..." : "Ejecutar Estimación"}
      </button>
      <div className="logs-container">
        <h3>Registro de Procesos:</h3>
        <pre>{logs.join("\n")}</pre>
      </div>
    </div>
  );
}
