import React, { useEffect, useState } from "react";
import "./excel_preview.css";

const MAX_ROWS = 200;

export interface OutputFilesMap {
  con_libranza?: string;
  sin_libranza?: string;
}

interface ExcelPreviewProps {
  outputFiles: OutputFilesMap | null;
  isProcessing?: boolean;
  errorMessage?: string | null;
}

type TabKey = "con" | "sin";

interface SheetPreview {
  headers: string[];
  rows: (string | number | boolean)[][];
}

function cellToString(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "boolean") return v ? "TRUE" : "FALSE";
  return String(v);
}

function parseExcelPath(absPath: string): SheetPreview | null {
  const req = (window as any).require as ((id: string) => unknown) | undefined;
  if (!req) return null;
  const fs = req("fs") as typeof import("fs");
  const XLSX = req("xlsx") as typeof import("xlsx");
  if (!fs.existsSync(absPath)) return null;
  const buf = fs.readFileSync(absPath);
  const wb = XLSX.read(buf, { type: "buffer", cellDates: true });
  const sheetName = wb.SheetNames[0];
  if (!sheetName) return { headers: [], rows: [] };
  const sheet = wb.Sheets[sheetName];
  const matrix = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    defval: "",
    raw: false,
  }) as unknown[][];
  const capped = matrix.slice(0, MAX_ROWS + 1);
  const headers = (capped[0] ?? []).map((h) => cellToString(h));
  const rows = capped.slice(1).map((row) =>
    headers.map((_, i) => cellToString((row as unknown[])[i])),
  );
  return { headers, rows };
}

export default function ExcelPreview({
  outputFiles,
  isProcessing,
  errorMessage,
}: ExcelPreviewProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("con");
  const [preview, setPreview] = useState<SheetPreview | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const hasCon = Boolean(outputFiles?.con_libranza);
  const hasSin = Boolean(outputFiles?.sin_libranza);

  useEffect(() => {
    if (!hasCon && hasSin) setActiveTab("sin");
    if (hasCon && !hasSin) setActiveTab("con");
  }, [hasCon, hasSin]);

  useEffect(() => {
    setLoadError(null);
    setPreview(null);

    if (isProcessing || !outputFiles) return;

    const path =
      activeTab === "con"
        ? outputFiles.con_libranza
        : outputFiles.sin_libranza;
    if (!path) {
      setLoadError("No hay archivo para esta pestaña.");
      return;
    }

    try {
      const req = (window as any).require;
      if (!req) {
        setLoadError(
          "La vista previa del Excel requiere la aplicación de escritorio.",
        );
        return;
      }
      const data = parseExcelPath(path);
      if (!data) {
        setLoadError("No se pudo leer el archivo.");
        return;
      }
      setPreview(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setLoadError(msg);
    }
  }, [outputFiles, activeTab, isProcessing]);

  const showTabs = hasCon || hasSin;

  return (
    <section className="card excel-preview-card">
      <div className="card-header">
        <span className="card-icon card-icon--red">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18M9 21V9" />
          </svg>
        </span>
        <h2 className="card-title">Vista previa del resultado</h2>
      </div>

      <div className="excel-preview-body">
        {isProcessing ? (
          <div className="excel-preview-state" role="status">
            <span className="excel-preview-spinner" aria-hidden />
            Generando archivos Excel…
          </div>
        ) : errorMessage ? (
          <div className="excel-preview-state excel-preview-state--error">
            {errorMessage}
          </div>
        ) : outputFiles === null ? (
          <div className="excel-preview-state">
            Ejecute el procesamiento para ver aquí una vista previa de{" "}
            <strong>PE_con_libranza.xlsx</strong> y{" "}
            <strong>PE_sin_libranza.xlsx</strong>.
          </div>
        ) : !hasCon && !hasSin ? (
          <div className="excel-preview-state">
            El proceso finalizó correctamente, pero no se generaron archivos de
            salida (carteras vacías).
          </div>
        ) : (
          <>
            {showTabs && (
              <div
                className="excel-preview-tabs"
                role="tablist"
                aria-label="Archivo de salida"
              >
                {hasCon && (
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeTab === "con"}
                    className={`excel-preview-tab${activeTab === "con" ? " excel-preview-tab--active" : ""}`}
                    onClick={() => setActiveTab("con")}
                  >
                    PE con libranza
                  </button>
                )}
                {hasSin && (
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeTab === "sin"}
                    className={`excel-preview-tab${activeTab === "sin" ? " excel-preview-tab--active" : ""}`}
                    onClick={() => setActiveTab("sin")}
                  >
                    PE sin libranza
                  </button>
                )}
              </div>
            )}

            {loadError ? (
              <div className="excel-preview-state excel-preview-state--error">
                {loadError}
              </div>
            ) : preview && preview.headers.length > 0 ? (
              <div className="excel-preview-scroll">
                <table className="excel-preview-table">
                  <thead>
                    <tr>
                      {preview.headers.map((h, i) => (
                        <th key={i} title={h}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row, ri) => (
                      <tr key={ri}>
                        {preview.headers.map((_, ci) => (
                          <td key={ci} title={String(row[ci] ?? "")}>
                            {row[ci] ?? ""}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="excel-preview-state">Sin datos en la hoja.</div>
            )}

            {preview && preview.headers.length > 0 && (
              <p className="excel-preview-hint">
                Vista previa: máximo {MAX_ROWS} filas. El archivo completo está
                en la carpeta de salida.
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
