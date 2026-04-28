import { useState } from "react";
import logo from "../../assets/logo-ctx-final.png";
import "./header.css";
import { IoMdHelpCircle } from "react-icons/io";

export default function Header() {
  const [showHelp, setShowHelp] = useState(false);

  return (
    <>
      <header className="header">
        <div className="header__brand">
          <div className="header__logo">
            <img src={logo} alt="Logo" />
          </div>
        </div>

        <div className="header__module">
          <h1>ESTIMADOR DE PÉRDIDA ESPERADA</h1>
          <p>Módulo de Riesgo Crediticio</p>
        </div>

        <div className="header__icons">
          <span onClick={() => setShowHelp(true)} style={{ cursor: "pointer" }}>
            <IoMdHelpCircle />
          </span>
        </div>
      </header>

      {showHelp && (
        <div className="help-overlay" onClick={() => setShowHelp(false)}>
        <div className="help-modal" onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}>
          <h3>📊 Modelo de Pérdida Esperada</h3>
          <p>Según el Anexo 2 del Capítulo II de la Circular Básica Contable y Financiera de la <strong>Supersolidaria</strong>, la pérdida esperada se calcula así:</p>

          <div className="help-formula">
            PERDIDA ESPERADA = PI × VEA × PDI
          </div>

          <ul>
            <li><strong>PI — Probabilidad de Incumplimiento:</strong> Probabilidad de que el deudor incumpla en los próximos 12 meses, según la modalidad de cartera y calificación (A, B, C, D, E).</li>
            <li><strong>VEA — Valor Expuesto del Activo:</strong> Saldo de la obligación al momento del cálculo, incluyendo intereses y descontando aportes y ahorro permanente.</li>
            <li><strong>PDI — Pérdida Dado el Incumplimiento:</strong> Deterioro económico estimado en caso de incumplimiento, según el tipo de garantía (idónea, no idónea o sin garantía).</li>
          </ul>

          <p>El sistema aplica tres modelos según la modalidad de cartera:</p>
          <ul>
            <li>🔹 <strong>Consumo con libranza</strong> — requiere descuento por nómina activo.</li>
            <li>🔹 <strong>Consumo sin libranza</strong> — créditos de consumo sin descuento por nómina.</li>
            <li>🔹 <strong>Comercial persona natural</strong> — cartera comercial de personas naturales.</li>
          </ul>

          <p>La calificación de cada deudor (A a E) se determina mediante una función logística basada en variables de mora y características del crédito.</p>

          <button onClick={() => setShowHelp(false)}>Cerrar</button>
        </div>
        </div>
      )}
      <hr />
    </>
  );
}