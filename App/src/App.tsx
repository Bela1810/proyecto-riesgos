import { useState } from "react";
import Header from "./components/layout/header";
import { MdCalendarMonth } from "react-icons/md";
import "./index.css";
import Form from "./components/ui/form";
import ExcelPreview, {
  type OutputFilesMap,
} from "./components/ui/excel_preview";

const formatLastRun = (date: Date): string => {
  const today = new Date();
  const isToday = date.toDateString() === today.toDateString();

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();

  return isToday
    ? `${day}/${month}/${year}`
    : `${day}/${month}/${year}`;
};

export function App() {
  const [inputPath, setInputPath] = useState("");
  const [outputPath, setOutputPath] = useState("");
  const [outputFiles, setOutputFiles] = useState<OutputFilesMap | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRun, setLastRun] = useState<Date | null>(() => {
    const saved = localStorage.getItem("lastRun");
    return saved ? new Date(saved) : null;
  });

  const handleExecute = async () => {
    if (!inputPath || !outputPath) {
      alert("Por favor, seleccione las carpetas de entrada y salida.");
      return;
    }

    const now = new Date();
    setLastRun(now);
    localStorage.setItem("lastRun", now.toISOString());

    setOutputFiles(null);
    setPreviewError(null);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5000/api/run-estimation", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          input_folder: inputPath,
          output_folder: outputPath,
        }),
      });

      const result = await response.json();

      if (result.status === "success") {
        setOutputFiles(result.files ?? {});
        setPreviewError(null);
      } else {
        setOutputFiles(null);
        setPreviewError(
          typeof result.message === "string"
            ? result.message
            : "Error en el proceso.",
        );
      }
    } catch (error: unknown) {
      console.error("Error al ejecutar la estimación:", error);
      const msg =
        error instanceof Error ? error.message : String(error);
      setOutputFiles(null);
      setPreviewError(`Error de conexión con el backend: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Header />
      <div className="page-header">
        <div className="page-header_title">
          <h2 className="title">Procesamiento de Datos 📊</h2>
          <p className="subtitle">
            Configure las rutas de origen y destino para calcular la pérdida
            esperada basándose en los modelos vigentes
          </p>
        </div>
        <div className="page-header_last">
          <span className="badge-last-run">
            <MdCalendarMonth size={23} color={"#c0161d"} />
            Última ejecución: {lastRun ? formatLastRun(lastRun) : "Nunca"}
          </span>
        </div>
      </div>
      <main className="main-content">
        <Form
          inputPath={inputPath}
          setInputPath={setInputPath}
          outputPath={outputPath}
          setOutputPath={setOutputPath}
          onExecute={handleExecute}
          isLoading={isLoading}
        />
        <ExcelPreview
          outputFiles={outputFiles}
          isProcessing={isLoading}
          errorMessage={previewError}
        />
      </main>
    </div>
  );
}

export default App;
