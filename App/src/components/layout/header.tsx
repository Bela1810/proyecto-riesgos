import React from "react";
import logo from "../../assets/logo-ctx-final.png";
import "./header.css";
import { IoMdHelpCircle } from "react-icons/io";

export default function Header() {
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
            <IoMdHelpCircle />
        </div>
      </header>

      <hr />
    </>
  );

}