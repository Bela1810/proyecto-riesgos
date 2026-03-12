import React, { useState } from "react";
import "./form.css";
import { ImFolderDownload } from "react-icons/im";
import { FaPlay, FaFolder, FaFolderPlus } from "react-icons/fa";

export default function Form() {

  const [inputPath, setInputPath] = useState("");
  const [outputPath, setOutputPath] = useState("");

  const ipcRenderer =
    (window as any)?.require?.("electron")?.ipcRenderer;

  async function openInput() {
    if (!ipcRenderer) return;

    const folder = await ipcRenderer.invoke("select-folder");
    if (folder) setInputPath(folder);
  }

  async function openOutput() {
    if (!ipcRenderer) return;

    const folder = await ipcRenderer.invoke("select-folder");
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
          <label>Carpeta de Archivos (Entrada)</label>

          <div className="input-with-icon">
            <input
              type="text"
              value={inputPath}
              placeholder="Seleccione carpeta de entrada..."
              readOnly
            />

            <span className="icon-folder" onClick={openInput}>
              <FaFolder size={27} color="#e01b24" />
            </span>
          </div>

          <p>Seleccione el directorio que contiene los archivos de cartera</p>
        </div>

        <div className="directory-input">
          <label>Carpeta de Salida (Resultados)</label>

          <div className="input-with-icon">
            <input
              type="text"
              value={outputPath}
              placeholder="Seleccione ubicación de salida..."
              readOnly
            />

            <span className="icon-folder" onClick={openOutput}>
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