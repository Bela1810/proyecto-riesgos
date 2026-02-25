import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, ttk

import joblib
import numpy as np
import pandas as pd

# --- Funciones de Lógica de Negocio (Sin cambios mayores) ---

meses_es = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


def mes_ano_to_date(mes_ano, log_func):
    try:
        mes, ano = mes_ano.split("_")
        return pd.Timestamp(year=int(ano), month=meses_es[mes], day=1)
    except Exception as e:
        log_func(
            f"Error al convertir fecha del archivo: {mes_ano}. Error: {e}", "error"
        )
        return None


def calcular_pdi(row):
    clase = row["clasegarantia"]
    morosidad = row["Morosidad"]

    if clase in [1, 4]:
        if morosidad >= 420:
            return 1.0
        elif morosidad >= 210:
            return 0.7
        elif morosidad >= 90:
            return 0.6
        else:
            return 0.45
    elif clase == 2:
        if morosidad >= 720:
            return 1.0
        elif morosidad >= 360:
            return 0.7
        else:
            return 0.4
    elif clase == 3:
        if morosidad >= 540:
            return 1.0
        elif morosidad >= 270:
            return 0.7
        else:
            return 0.5
    else:
        return np.nan


# --- Clase de la Aplicación de Escritorio ---


class PEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estimador de Pérdida Esperada (PE)")
        self.root.geometry("700x600")

        # Estilos
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")

        # Variables de control
        self.carpeta_base = tk.StringVar()
        self.carpeta_salida = tk.StringVar()

        # --- Interfaz ---
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título y descripción
        lbl_title = ttk.Label(
            main_frame,
            text="Estimador de Pérdida Esperada (PE)",
            font=("Helvetica", 16, "bold"),
        )
        lbl_title.pack(pady=(0, 10))

        lbl_desc = ttk.Label(
            main_frame,
            text="Procesamiento de archivos de cartera y aplicación de modelos ML.",
            wraplength=600,
        )
        lbl_desc.pack(pady=(0, 20))

        # Selector Carpeta Entrada
        frm_input = ttk.LabelFrame(
            main_frame, text="Carpeta de Archivos (Entrada)", padding="10"
        )
        frm_input.pack(fill=tk.X, pady=5)

        entry_input = ttk.Entry(frm_input, textvariable=self.carpeta_base)
        entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        btn_input = ttk.Button(
            frm_input,
            text="📂 Buscar",
            command=lambda: self.seleccionar_carpeta(self.carpeta_base),
        )
        btn_input.pack(side=tk.RIGHT)

        # Selector Carpeta Salida
        frm_output = ttk.LabelFrame(
            main_frame, text="Carpeta Salida (Resultados)", padding="10"
        )
        frm_output.pack(fill=tk.X, pady=5)

        entry_output = ttk.Entry(frm_output, textvariable=self.carpeta_salida)
        entry_output.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        btn_output = ttk.Button(
            frm_output,
            text="📂 Buscar",
            command=lambda: self.seleccionar_carpeta(self.carpeta_salida),
        )
        btn_output.pack(side=tk.RIGHT)

        # Botón Ejecutar
        self.btn_run = ttk.Button(
            main_frame, text="▶ Ejecutar Estimación", command=self.iniciar_proceso
        )
        self.btn_run.pack(pady=20, fill=tk.X)

        # Barra de Progreso
        self.progress = ttk.Progressbar(
            main_frame, orient=tk.HORIZONTAL, length=100, mode="determinate"
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # Consola de Logs
        lbl_logs = ttk.Label(main_frame, text="Registro de Procesos:")
        lbl_logs.pack(anchor="w")
        self.txt_logs = scrolledtext.ScrolledText(
            main_frame, height=12, state="disabled", font=("Consolas", 9)
        )
        self.txt_logs.pack(fill=tk.BOTH, expand=True)

    def log(self, message, type="info"):
        """Función para escribir en la consola de la GUI de forma segura desde hilos."""

        def _log():
            self.txt_logs.config(state="normal")
            prefix = "❌ " if type == "error" else "⚠️ " if type == "warning" else "ℹ️ "
            self.txt_logs.insert(tk.END, f"{prefix}{message}\n")
            self.txt_logs.see(tk.END)
            self.txt_logs.config(state="disabled")

        self.root.after(0, _log)

    def update_progress(self, value):
        self.root.after(0, lambda: self.progress.config(value=value))

    def seleccionar_carpeta(self, var_store):
        folder = filedialog.askdirectory()
        if folder:
            var_store.set(folder)

    def iniciar_proceso(self):
        base = self.carpeta_base.get()
        salida = self.carpeta_salida.get()

        if not base or not salida:
            messagebox.showwarning(
                "Faltan datos", "Por favor seleccione ambas carpetas."
            )
            return

        # Deshabilitar botón para evitar doble clic
        self.btn_run.config(state="disabled")
        self.txt_logs.config(state="normal")
        self.txt_logs.delete(1.0, tk.END)
        self.txt_logs.config(state="disabled")

        # Ejecutar en un hilo separado para no congelar la GUI
        thread = threading.Thread(target=self.procesar_datos, args=(base, salida))
        thread.daemon = True
        thread.start()

    def procesar_datos(self, carpeta_base, carpeta_salida):
        try:
            self.log("Iniciando proceso...", "info")
            self.update_progress(5)

            # 1. Descubrimiento de Archivos
            if not os.path.exists(carpeta_base):
                self.log(f"La carpeta base no existe: {carpeta_base}", "error")
                return

            archivos_en_base = os.listdir(carpeta_base)

            archivos_credito = [
                f
                for f in archivos_en_base
                if "CREDITO" in f.upper() and f.endswith(".xlsx")
            ]
            archivo_asociados = next(
                (
                    f
                    for f in archivos_en_base
                    if "ASOCIADOS" in f.upper() and f.endswith(".xlsx")
                ),
                None,
            )
            archivo_aportes = next(
                (
                    f
                    for f in archivos_en_base
                    if "APORTES" in f.upper() and f.endswith(".xlsx")
                ),
                None,
            )
            archivo_captaciones = next(
                (
                    f
                    for f in archivos_en_base
                    if "CAPTACIONES" in f.upper() and f.endswith(".xlsx")
                ),
                None,
            )

            modelo_con_path = next(
                (
                    os.path.join(carpeta_base, f)
                    for f in archivos_en_base
                    if f.endswith(".joblib") and "con" in f.lower()
                ),
                None,
            )
            modelo_sin_path = next(
                (
                    os.path.join(carpeta_base, f)
                    for f in archivos_en_base
                    if f.endswith(".joblib") and "sin" in f.lower()
                ),
                None,
            )

            if not archivos_credito:
                self.log("No se encontraron archivos de CRÉDITO.", "error")
                return
            if not archivo_asociados:
                self.log("No se encontró el archivo de ASOCIADOS.", "error")
                return
            if not modelo_con_path or not modelo_sin_path:
                self.log("No se encontraron los modelos .joblib.", "error")
                return

            self.log(
                f"Archivos encontrados: {len(archivos_credito)} créditos, Asociados, Aportes ({'Sí' if archivo_aportes else 'No'}), Captaciones ({'Sí' if archivo_captaciones else 'No'})."
            )

            # 2. Cargar y Procesar Archivos de Crédito
            dataframes = {}
            total_archivos = len(archivos_credito)

            for i, archivo in enumerate(archivos_credito):
                try:
                    nombre_df = archivo.split(".")[0]
                    if "_" in nombre_df:
                        parts = nombre_df.split("_")
                        if len(parts) >= 3:
                            nombre_df = f"{parts[-2]}_{parts[-1]}"
                        elif len(parts) == 2:
                            nombre_df = parts[1]

                    ruta_archivo = os.path.join(carpeta_base, archivo)
                    df_temp = pd.read_excel(ruta_archivo, header=3)

                    cols_req = [
                        "NIT",
                        "NroCredito",
                        "CodigoContable",
                        "Morosidad",
                        "ValorPrestamo",
                        "SaldoCapital",
                        "SaldoIntereses",
                        "OtrosSaldos",
                        "clasegarantia",
                    ]
                    missing_cols = [c for c in cols_req if c not in df_temp.columns]

                    if missing_cols:
                        self.log(
                            f"Archivo {archivo} incompleto. Faltan: {missing_cols}",
                            "warning",
                        )
                        continue

                    df_temp = (
                        df_temp[cols_req]
                        .dropna(subset=["NroCredito"])
                        .drop_duplicates(subset=["NroCredito"])
                        .set_index("NroCredito")
                    )
                    df_temp["SALPRES"] = (
                        df_temp["SaldoCapital"] / df_temp["ValorPrestamo"]
                    )
                    df_temp["VEA"] = (
                        df_temp["SaldoCapital"]
                        + df_temp["SaldoIntereses"]
                        + df_temp["OtrosSaldos"]
                    )

                    dataframes[nombre_df] = df_temp

                    # Progreso parcial (hasta 20%)
                    self.update_progress(5 + (i + 1) / total_archivos * 15)
                    self.log(f"Leído: {archivo}")

                except Exception as e:
                    self.log(f"Error leyendo {archivo}: {e}", "warning")

            if not dataframes:
                self.log("No hay datos válidos para procesar.", "error")
                return

            # 3. Ordenar y Fusionar
            self.log("Fusionando históricos...")
            meses_ordenados = sorted(
                dataframes.keys(), key=lambda x: mes_ano_to_date(x, self.log)
            )

            if not meses_ordenados:
                self.log("Error ordenando meses.", "error")
                return

            df_mora = dataframes[meses_ordenados[0]][
                ["NIT", "Morosidad", "CodigoContable", "SALPRES", "VEA"]
            ].copy()
            suffix = f"_{meses_ordenados[0]}"
            df_mora = df_mora.rename(
                columns=lambda x: x + suffix
                if x
                in [
                    "Morosidad",
                    "CodigoContable",
                    "NIT",
                    "SALPRES",
                    "VEA",
                    "clasegarantia",
                ]
                else x
            )
            df_mora = df_mora.rename(
                columns={"clasegarantia": f"clasegarantia{suffix}"}
            )  # Asegurar renombrado si no cae en lambda

            # Ajuste manual para el renombrado inicial correcto basado en lógica original
            cols_rename = {
                "Morosidad": f"Morosidad_{meses_ordenados[0]}",
                "CodigoContable": f"CodigoContable_{meses_ordenados[0]}",
                "NIT": f"NIT_{meses_ordenados[0]}",
                "SALPRES": f"SALPRES_{meses_ordenados[0]}",
                "VEA": f"VEA_{meses_ordenados[0]}",
                "clasegarantia": f"clasegarantia_{meses_ordenados[0]}",
            }
            # Recargar para asegurar limpieza (el lambda anterior puede ser confuso)
            df_mora = dataframes[meses_ordenados[0]][
                [
                    "NIT",
                    "Morosidad",
                    "CodigoContable",
                    "SALPRES",
                    "VEA",
                    "clasegarantia",
                ]
            ].rename(columns=cols_rename)

            for i, mes in enumerate(meses_ordenados[1:]):
                df_temp = dataframes[mes][
                    [
                        "NIT",
                        "Morosidad",
                        "CodigoContable",
                        "SALPRES",
                        "VEA",
                        "clasegarantia",
                    ]
                ].rename(
                    columns={
                        "Morosidad": f"Morosidad_{mes}",
                        "CodigoContable": f"CodigoContable_{mes}",
                        "NIT": f"NIT_{mes}",
                        "SALPRES": f"SALPRES_{mes}",
                        "VEA": f"VEA_{mes}",
                        "clasegarantia": f"clasegarantia_{mes}",
                    }
                )
                df_mora = df_mora.merge(
                    df_temp, left_index=True, right_index=True, how="outer"
                )
                self.update_progress(20 + (i + 1) / len(meses_ordenados[1:]) * 20)

            # 4. Variables Derivadas
            self.log("Calculando MORA12 y PDI...")
            last_month = meses_ordenados[-1]
            df_mora = df_mora.dropna(subset=[f"NIT_{last_month}"])

            df_mora[f"MORA12_{last_month}"] = df_mora.filter(like="Morosidad").max(
                axis=1, skipna=True
            )

            new_column_names = {
                f"Morosidad_{last_month}": "Morosidad",
                f"CodigoContable_{last_month}": "CodigoContable",
                f"NIT_{last_month}": "NIT",
                f"SALPRES_{last_month}": "SALPRES",
                f"VEA_{last_month}": "VEA",
                f"MORA12_{last_month}": "MORA12",
                f"clasegarantia_{last_month}": "clasegarantia",
            }
            df_mora = (
                df_mora[list(new_column_names.keys())]
                .rename(columns=new_column_names)
                .reset_index()
            )

            df_mora["SINMORA"] = np.where(df_mora["MORA12"] == 0, 1, 0)
            df_mora["PDI"] = df_mora.apply(calcular_pdi, axis=1)

            self.update_progress(50)

            # 5. Asociados
            self.log("Procesando Asociados...")
            ruta_asociados = os.path.join(carpeta_base, archivo_asociados)
            # Heurística simple para fecha de corte asociados
            try:
                ultimo_dia_mes = mes_ano_to_date(
                    last_month, self.log
                ) + pd.offsets.MonthEnd(0)
            except:
                ultimo_dia_mes = datetime.now()

            df_asociados = pd.read_excel(ruta_asociados, header=3)
            df_asociados["Fecha de ingreso"] = pd.to_datetime(
                df_asociados["Fecha de ingreso"], errors="coerce", format="%d/%m/%Y"
            )
            df_asociados["Activo"] = df_asociados["Activo"].fillna(1).astype(int)
            df_asociados["ANTI"] = (
                df_asociados["Activo"]
                * (ultimo_dia_mes - df_asociados["Fecha de ingreso"]).dt.days
            )

            df_mora["NIT"] = df_mora["NIT"].astype(str)
            df_asociados["Número de identificación"] = df_asociados[
                "Número de identificación"
            ].astype(str)

            df_features = pd.merge(
                df_mora,
                df_asociados[["Número de identificación", "Activo", "ANTI"]],
                left_on="NIT",
                right_on="Número de identificación",
                how="left",
            ).drop(columns=["Número de identificación"])
            self.update_progress(60)

            # 6. Aportes
            if archivo_aportes:
                self.log("Procesando Aportes...")
                ruta_aportes = os.path.join(carpeta_base, archivo_aportes)
                df_aportes = pd.read_excel(ruta_aportes, header=3)
                df_aportes["Aporte/Contribución Ordinario"] = df_aportes[
                    "Aporte/Contribución Ordinario"
                ].fillna(0)
                df_aportes = df_aportes.rename(
                    columns={"Aporte/Contribución Ordinario": "AP"}
                )
                df_aportes["Número de identificación"] = df_aportes[
                    "Número de identificación"
                ].astype(str)
                df_features = pd.merge(
                    df_features,
                    df_aportes[["Número de identificación", "AP"]],
                    left_on="NIT",
                    right_on="Número de identificación",
                    how="left",
                ).drop(columns=["Número de identificación"])
            else:
                df_features["AP"] = 0
            self.update_progress(70)

            # 7. Captaciones
            if archivo_captaciones:
                self.log("Procesando Captaciones...")
                ruta_captaciones = os.path.join(carpeta_base, archivo_captaciones)
                df_captaciones = pd.read_excel(ruta_captaciones, header=3)
                df_captaciones["es CDAT"] = (
                    df_captaciones["NombreDeposito"]
                    .str.contains("CDAT", case=False, na=False)
                    .astype(int)
                )
                df_captaciones["COOCDAT"] = (
                    df_captaciones["es CDAT"] * df_captaciones["Saldo"]
                )
                df_captaciones = df_captaciones[df_captaciones["es CDAT"] == 1][
                    ["NIT", "COOCDAT"]
                ]
                df_captaciones["NIT"] = df_captaciones["NIT"].astype(str)
                df_captaciones = df_captaciones.groupby("NIT").sum().reset_index()
                df_features = pd.merge(
                    df_features, df_captaciones, on="NIT", how="left"
                )
            else:
                df_features["COOCDAT"] = 0
            self.update_progress(80)

            # 8. Modelos
            self.log("Ejecutando Modelos ML...")
            lgbm_con = joblib.load(modelo_con_path)
            lgbm_sin = joblib.load(modelo_sin_path)

            cod_con_libranza = [
                141105,
                141110,
                141115,
                141120,
                144105,
                144110,
                144115,
                144120,
                144125,
            ]

            df_con = df_features[
                df_features["CodigoContable"].isin(cod_con_libranza)
            ].copy()
            df_sin = df_features[
                ~df_features["CodigoContable"].isin(cod_con_libranza)
            ].copy()

            # Lógica Con Libranza
            if not df_con.empty:
                df_con["COOCDAT"] = df_con["COOCDAT"].fillna(0)
                df_con = df_con[df_con["Activo"] == 1]
                df_con["AP"] = df_con["AP"].fillna(0)
                vars_con = ["AP", "COOCDAT", "MORA12", "SINMORA", "ANTI"]
                for col in vars_con:
                    if col not in df_con.columns:
                        df_con[col] = 0

                df_con["Calif.modelo"] = lgbm_con.predict(df_con[vars_con])
                df_con["Calif.modelo"] = df_con["Calif.modelo"].map(
                    {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}
                )

                # Lógica de homologación (simplificada para legibilidad, igual a original)
                condiciones = [
                    (df_con["Calif.modelo"] == "A"),
                    (df_con["Calif.modelo"] == "B") & (df_con["MORA12"] <= 30),
                    (df_con["Calif.modelo"] == "B")
                    & (df_con["MORA12"] > 30)
                    & (df_con["MORA12"] < 90),
                    (df_con["Calif.modelo"] == "C") & (df_con["MORA12"] <= 30),
                    (df_con["Calif.modelo"] == "C")
                    & (df_con["MORA12"] > 30)
                    & (df_con["MORA12"] < 90),
                    (df_con["Calif.modelo"].isin(["D", "E"])),
                    (df_con["MORA12"].between(90, 180)),
                ]
                df_con["Calif.homologada"] = np.select(
                    condiciones, ["A", "A", "B", "B", "C", "C", "D"], default="E"
                )

            # Lógica Sin Libranza
            if not df_sin.empty:
                df_sin[["Activo", "ANTI", "AP"]] = df_sin[
                    ["Activo", "ANTI", "AP"]
                ].fillna(0)
                vars_sin = ["Activo", "ANTI", "SALPRES", "AP", "MORA12"]
                for col in vars_sin:
                    if col not in df_sin.columns:
                        df_sin[col] = 0

                df_sin["Calif.modelo"] = lgbm_sin.predict(df_sin[vars_sin])
                df_sin["Calif.modelo"] = df_sin["Calif.modelo"].map(
                    {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}
                )

                condiciones = [
                    (df_sin["Calif.modelo"] == "A"),
                    (df_sin["Calif.modelo"] == "B") & (df_sin["MORA12"] <= 30),
                    (df_sin["Calif.modelo"] == "B")
                    & (df_sin["MORA12"] > 30)
                    & (df_sin["MORA12"] < 90),
                    (df_sin["Calif.modelo"] == "C") & (df_sin["MORA12"] <= 30),
                    (df_sin["Calif.modelo"] == "C")
                    & (df_sin["MORA12"] > 30)
                    & (df_sin["MORA12"] < 90),
                    (df_sin["Calif.modelo"].isin(["D", "E"])),
                    (df_sin["MORA12"].between(90, 180)),
                ]
                df_sin["Calif.homologada"] = np.select(
                    condiciones, ["A", "A", "B", "B", "C", "C", "D"], default="E"
                )

            # Calculo PI y PE final
            df_peor_calificacion = pd.concat(
                [
                    df_con[["NIT", "Calif.homologada"]],
                    df_sin[["NIT", "Calif.homologada"]],
                ]
            )
            if not df_peor_calificacion.empty:
                df_peor_calificacion = (
                    df_peor_calificacion.groupby("NIT")["Calif.homologada"]
                    .max()
                    .reset_index()
                )

                # Mapeo final
                mapa_pi_con = {
                    "A": 0.005,
                    "B": 0.006,
                    "C": 0.0441,
                    "D": 0.0448,
                    "E": 0.2273,
                }
                mapa_pi_sin = {
                    "A": 0.015,
                    "B": 0.0595,
                    "C": 0.1382,
                    "D": 0.3277,
                    "E": 0.4171,
                }

                if not df_con.empty:
                    df_con["Calif.final"] = df_con["NIT"].map(
                        df_peor_calificacion.set_index("NIT")["Calif.homologada"]
                    )
                    df_con["PI"] = df_con["Calif.final"].map(mapa_pi_con).astype(float)
                    df_con["PE"] = df_con["PI"] * df_con["VEA"] * df_con["PDI"]

                if not df_sin.empty:
                    df_sin["Calif.final"] = df_sin["NIT"].map(
                        df_peor_calificacion.set_index("NIT")["Calif.homologada"]
                    )
                    df_sin["PI"] = df_sin["Calif.final"].map(mapa_pi_sin).astype(float)
                    df_sin["PE"] = df_sin["PI"] * df_sin["VEA"] * df_sin["PDI"]

            self.update_progress(90)

            # 9. Guardar
            self.log("Guardando resultados...")
            ruta_con = os.path.join(carpeta_salida, "PE_con_libranza.xlsx")
            ruta_sin = os.path.join(carpeta_salida, "PE_sin_libranza.xlsx")

            if not df_con.empty:
                df_con.to_excel(ruta_con, index=False)
                self.log(f"✅ Guardado: {ruta_con}")
            else:
                self.log("⚠️ No se generaron datos Con Libranza", "warning")

            if not df_sin.empty:
                df_sin.to_excel(ruta_sin, index=False)
                self.log(f"✅ Guardado: {ruta_sin}")
            else:
                self.log("⚠️ No se generaron datos Sin Libranza", "warning")

            self.update_progress(100)
            self.log("¡PROCESO FINALIZADO CON ÉXITO!", "info")
            messagebox.showinfo("Éxito", "El proceso ha finalizado correctamente.")

        except Exception as e:
            self.log(f"ERROR CRÍTICO: {str(e)}", "error")
            import traceback

            traceback.print_exc()
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        finally:
            # Reactivar botón
            self.root.after(0, lambda: self.btn_run.config(state="normal"))


if __name__ == "__main__":
    root = tk.Tk()
    app = PEApp(root)
    root.mainloop()
