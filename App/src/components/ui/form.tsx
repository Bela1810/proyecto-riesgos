import React, { useState } from "react";
import "./form.css";
import { ImFolderDownload } from "react-icons/im";
import { FaPlay, FaFolder, FaFolderPlus } from "react-icons/fa";

export default function Form() {

  const [inputPath, setInputPath] = useState("");
  const [outputPath, setOutputPath] = useState("");

  const ipcRenderer =
    (window as any)?.require?.("electron")?.ipcRenderer;

  async function pickExcelInBrowser(): Promise<string | null> {
    return new Promise((resolve) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel";

      input.onchange = () => {
        const file = input.files?.[0];
        resolve(file?.name ?? null);
      };

      input.oncancel = () => resolve(null);
      input.click();
    });
  }

  async function pickFolderInBrowser(): Promise<string | null> {
    const browserWindow = window as any;

    // Chromium API fallback when running outside Electron.
    if (typeof browserWindow.showDirectoryPicker === "function") {
      try {
        const handle = await browserWindow.showDirectoryPicker();
        return handle?.name ?? null;
      } catch {
        return null;
      }
    }

    return new Promise((resolve) => {
      const input = document.createElement("input");
      input.type = "file";
      input.setAttribute("webkitdirectory", "");
      input.setAttribute("directory", "");
      input.multiple = true;

      input.onchange = () => {
        const file = input.files?.[0] as File & { webkitRelativePath?: string };
        const folderName = file?.webkitRelativePath?.split("/")[0] ?? null;
        resolve(folderName);
      };

      input.oncancel = () => resolve(null);
      input.click();
    });
  }

  async function selectFolder(): Promise<string | null> {
    if (ipcRenderer) {
      const folder = await ipcRenderer.invoke("select-folder");
      return folder ?? null;
    }

    return pickFolderInBrowser();
  }

  async function selectExcelFile(): Promise<string | null> {
    if (ipcRenderer) {
      const filePath = await ipcRenderer.invoke("select-excel-file");
      return filePath ?? null;
    }

    return pickExcelInBrowser();
  }

  async function openInput() {
    const filePath = await selectExcelFile();
    if (filePath) setInputPath(filePath);
  }

  async function openOutput() {
    const folder = await selectFolder();
    if (folder) setOutputPath(folder);
  }

  return (
    <section className="card">

      <div className="card-header">
        <span className="card-icon">
          <ImFolderDownload size={23} color="#c0161d" />
        </span>
        <h2>Configuración de Directorios</h2>
      </div>

      <hr className="card-divider" />

      <div className="card-body">

        <div className="directory-input">
          <label>Archivo Excel (Entrada)</label>

          <div className="input-with-icon">
            <input
              type="text"
              value={inputPath}
              placeholder="Seleccione archivo Excel de entrada..."
              readOnly
              onClick={openInput}
            />

            <span
              className="icon-folder"
              onClick={openInput}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  void openInput();
                }
              }}
            >
              <FaFolder size={27} color="#e01b24" />
            </span>
          </div>

          <p>Seleccione el archivo Excel que contiene los datos de cartera</p>
        </div>

        <div className="directory-input">
          <label>Carpeta de Salida (Resultados)</label>

          <div className="input-with-icon">
            <input
              type="text"
              value={outputPath}
              placeholder="Seleccione ubicación de salida..."
              readOnly
              onClick={openOutput}
            />

            <span
              className="icon-folder"
              onClick={openOutput}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  void openOutput();
                }
              }}
            >
              <FaFolderPlus size={27} color="#e01b24" />
            </span>
          </div>

          <p>
            Los reportes finales se generarán en formato Excel en esta ubicación
          </p>
        </div>

        <div className="card-footer">
          <button className="btn-execute">
            <FaPlay />
            EJECUTAR ESTIMACIÓN
          </button>

          <p className="config-card__note">
            El proceso puede tardar unos minutos dependiendo del volumen de los datos
          </p>
        </div>

      </div>

    </section>
  );
}