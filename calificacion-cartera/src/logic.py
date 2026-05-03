import os
from datetime import datetime
import sys
import joblib
import numpy as np
import pandas as pd

meses_es = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
    "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}

def get_models_root(project_root):
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # extracted temp folder at runtime
    return project_root      # normal dev path


def mes_ano_to_date(mes_ano, log_func):
    try:
        mes, ano = mes_ano.split("_")
        return pd.Timestamp(year=int(ano), month=meses_es[mes], day=1)
    except Exception as e:
        log_func(f"Error al convertir fecha del archivo: {mes_ano}. Error: {e}", "error")
        return None

def calcular_pdi(row):
    clase = row["clasegarantia"]
    morosidad = row["Morosidad"]

    if clase in [1, 4, 6]:
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

def find_files(start_path, file_substring, extension):
    found_files = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file_substring.lower() in file.lower() and file.endswith(extension) and not file.startswith('~$'):
                found_files.append(os.path.join(root, file))
    return found_files

def find_file(start_path, file_substring, extension):
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file_substring.lower() in file.lower() and file.endswith(extension) and not file.startswith('~$'):
                return os.path.join(root, file)
    return None

def run_estimation_process(carpeta_base, carpeta_salida, log_func):
    try:
        log_func("Iniciando proceso...", "info")

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        if not os.path.exists(carpeta_base):
            log_func(f"La carpeta base no existe: {carpeta_base}", "error")
            return {"status": "error", "message": f"La carpeta base no existe: {carpeta_base}"}

        # Búsqueda recursiva de archivos
        log_func(f"Buscando archivos en: {carpeta_base}", "process")
        archivos_credito_paths = find_files(carpeta_base, "CREDITO", ".xlsx")
        archivo_asociados_path = find_file(carpeta_base, "ASOCIADOS", ".xlsx")

        models_root = get_models_root(project_root)
        modelo_con_path = find_file(models_root, "con_libranza", ".joblib")
        modelo_sin_path = find_file(models_root, "sin_libranza", ".joblib")

        log_func(f"Crédito: {len(archivos_credito_paths)}", "info")
        log_func(f"Asociados: {archivo_asociados_path}", "info")
        log_func(f"Mod con: {modelo_con_path}", "info")
        log_func(f"Mod sin: {modelo_sin_path}", "info")

        if not all([archivos_credito_paths, archivo_asociados_path, modelo_con_path, modelo_sin_path]):
            missing = []
            if not archivos_credito_paths: missing.append("archivos de CRÉDITO")
            if not archivo_asociados_path: missing.append("archivo de ASOCIADOS")
            if not modelo_con_path: missing.append("modelo con libranza (.joblib)")
            if not modelo_sin_path: missing.append("modelo sin libranza (.joblib)")

            error_msg = f"Faltan archivos esenciales: {', '.join(missing)}."
            log_func(error_msg, "error")
            return {"status": "error", "message": error_msg}

        log_func(f"Archivos de crédito encontrados: {len(archivos_credito_paths)}. Asociados: {'Sí' if archivo_asociados_path else 'No'}.")
        log_func(f"Modelo con libranza: {modelo_con_path}")
        log_func(f"Modelo sin libranza: {modelo_sin_path}")

        dataframes = {}
        for ruta_archivo in archivos_credito_paths:
            try:
                archivo_nombre = os.path.basename(ruta_archivo)
                nombre_df = archivo_nombre.split(".")[0]
                if "_" in nombre_df:
                    parts = nombre_df.split("_")
                    # Intenta extraer la parte de mes y año
                    nombre_df = f"{parts[-2]}_{parts[-1]}" if len(parts) >= 3 else parts[1]

                df_temp = pd.read_excel(ruta_archivo, header=3, engine="calamine")
                cols_req = ["NIT", "NroCredito", "CodigoContable", "Morosidad", "ValorPrestamo", "SaldoCapital", "SaldoIntereses", "OtrosSaldos", "clasegarantia"]
                if not all(c in df_temp.columns for c in cols_req):
                    log_func(f"Archivo {archivo_nombre} incompleto. Faltan columnas requeridas.", "warning")
                    continue

                df_temp = df_temp[cols_req].dropna(subset=["NroCredito"]).drop_duplicates(subset=["NroCredito"]).set_index("NroCredito")
                df_temp["SALPRES"] = df_temp["SaldoCapital"] / df_temp["ValorPrestamo"]
                df_temp["VEA"] = df_temp["SaldoCapital"] + df_temp["SaldoIntereses"] + df_temp["OtrosSaldos"]
                dataframes[nombre_df] = df_temp
                log_func(f"Leído: {archivo_nombre}", "process")
            except Exception as e:
                log_func(f"Error leyendo {ruta_archivo}: {e}", "warning")

        if not dataframes:
            log_func("No hay datos válidos para procesar.", "error")
            return {"status": "error", "message": "No se pudieron leer datos de crédito válidos."}

        log_func("Fusionando históricos...")
        meses_ordenados = sorted(dataframes.keys(), key=lambda x: mes_ano_to_date(x, log_func))
        if not meses_ordenados:
            log_func("Error ordenando meses.", "error")
            return {"status": "error", "message": "No se pudieron ordenar los archivos por fecha."}

        df_mora = dataframes[meses_ordenados[0]][["NIT", "Morosidad", "CodigoContable", "SALPRES", "VEA", "clasegarantia"]].copy()
        df_mora.rename(columns={col: f"{col}_{meses_ordenados[0]}" for col in df_mora.columns}, inplace=True)

        for mes in meses_ordenados[1:]:
            df_temp = dataframes[mes][["NIT", "Morosidad", "CodigoContable", "SALPRES", "VEA", "clasegarantia"]].copy()
            df_temp.rename(columns={col: f"{col}_{mes}" for col in df_temp.columns}, inplace=True)
            df_mora = df_mora.merge(df_temp, left_index=True, right_index=True, how="outer")

        log_func("Calculando MORA12 y PDI...")
        last_month = meses_ordenados[-1]
        df_mora.dropna(subset=[f"NIT_{last_month}"], inplace=True)
        df_mora[f"MORA12_{last_month}"] = df_mora.filter(like="Morosidad").max(axis=1, skipna=True)

        new_column_names = {
            f"Morosidad_{last_month}": "Morosidad", f"CodigoContable_{last_month}": "CodigoContable",
            f"NIT_{last_month}": "NIT", f"SALPRES_{last_month}": "SALPRES", f"VEA_{last_month}": "VEA",
            f"MORA12_{last_month}": "MORA12", f"clasegarantia_{last_month}": "clasegarantia",
        }
        df_mora = df_mora[list(new_column_names.keys())].rename(columns=new_column_names).reset_index()
        df_mora["SINMORA"] = np.where(df_mora["MORA12"] == 0, 1, 0)
        df_mora["PDI"] = df_mora.apply(calcular_pdi, axis=1)

        log_func("Procesando Asociados...")
        # ruta_asociados = os.path.join(carpeta_base, archivo_asociados)
        ultimo_dia_mes = mes_ano_to_date(last_month, log_func) + pd.offsets.MonthEnd(0) if mes_ano_to_date(last_month, log_func) else datetime.now()
        df_asociados = pd.read_excel(archivo_asociados_path, header=3, engine="calamine")
        df_asociados["Fecha de ingreso"] = pd.to_datetime(df_asociados["Fecha de ingreso"], errors="coerce", format="%d/%m/%Y")
        df_asociados["Activo"] = df_asociados["Activo"].fillna(1).astype(int)
        df_asociados["ANTI"] = (df_asociados["Activo"] * (ultimo_dia_mes - df_asociados["Fecha de ingreso"]).dt.days)
        df_mora["NIT"] = df_mora["NIT"].astype(str)
        df_asociados["Número de identificación"] = df_asociados["Número de identificación"].astype(str)
        df_features = pd.merge(df_mora, df_asociados[["Número de identificación", "Activo", "ANTI"]], left_on="NIT", right_on="Número de identificación", how="left").drop(columns=["Número de identificación"])

        # Búsqueda recursiva de archivos de aportes y captaciones
        archivo_aportes_path = find_file(carpeta_base, "APORTES", ".xlsx")
        archivo_captaciones_path = find_file(carpeta_base, "CAPTACIONES", ".xlsx")


        if archivo_aportes_path:
            log_func("Procesando Aportes...")
            df_aportes = pd.read_excel(archivo_aportes_path, header=3, engine="calamine")
            df_aportes["AP"] = df_aportes["Aporte/Contribución Ordinario"].fillna(0)
            df_aportes["Número de identificación"] = df_aportes["Número de identificación"].astype(str)
            df_features = pd.merge(df_features, df_aportes[["Número de identificación", "AP"]], left_on="NIT", right_on="Número de identificación", how="left").drop(columns=["Número de identificación"])
        else:
            df_features["AP"] = 0

        if archivo_captaciones_path:
            log_func("Procesando Captaciones...")
            df_captaciones = pd.read_excel(archivo_captaciones_path, header=3, engine="calamine")
            df_captaciones["es CDAT"] = df_captaciones["NombreDeposito"].str.contains("CDAT", case=False, na=False).astype(int)
            df_captaciones["COOCDAT"] = df_captaciones["es CDAT"] * df_captaciones["Saldo"]
            df_captaciones = df_captaciones[df_captaciones["es CDAT"] == 1][["NIT", "COOCDAT"]].groupby("NIT").sum().reset_index()
            df_captaciones["NIT"] = df_captaciones["NIT"].astype(str)
            df_features = pd.merge(df_features, df_captaciones, on="NIT", how="left")
        else:
            df_features["COOCDAT"] = 0

        log_func("Ejecutando Modelos ML...")
        lgbm_con = joblib.load(modelo_con_path)
        lgbm_sin = joblib.load(modelo_sin_path)
        cod_con_libranza = [141105, 141110, 141115, 141120, 144105, 144110, 144115, 144120, 144125]
        df_con = df_features[df_features["CodigoContable"].isin(cod_con_libranza)].copy()
        df_sin = df_features[~df_features["CodigoContable"].isin(cod_con_libranza)].copy()

        if not df_con.empty:
            df_con["COOCDAT"] = df_con["COOCDAT"].fillna(0)
            df_con = df_con[df_con["Activo"] == 1]
            df_con["AP"] = df_con["AP"].fillna(0)
            vars_con = ["AP", "COOCDAT", "MORA12", "SINMORA", "ANTI"]
            for col in vars_con:
                if col not in df_con.columns: df_con[col] = 0
            df_con["Calif.modelo"] = lgbm_con.predict(df_con[vars_con]).astype(str)
            df_con["Calif.modelo"] = df_con["Calif.modelo"].map({'0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E'})
            condiciones = [(df_con["Calif.modelo"] == "A"), (df_con["Calif.modelo"] == "B") & (df_con["MORA12"] <= 30), (df_con["Calif.modelo"] == "B") & (df_con["MORA12"] > 30) & (df_con["MORA12"] < 90), (df_con["Calif.modelo"] == "C") & (df_con["MORA12"] <= 30), (df_con["Calif.modelo"] == "C") & (df_con["MORA12"] > 30) & (df_con["MORA12"] < 90), (df_con["Calif.modelo"].isin(["D", "E"])), (df_con["MORA12"].between(90, 180))]
            df_con["Calif.homologada"] = np.select(condiciones, ["A", "A", "B", "B", "C", "C", "D"], default="E")

        if not df_sin.empty:
            df_sin[["Activo", "ANTI", "AP"]] = df_sin[["Activo", "ANTI", "AP"]].fillna(0)
            vars_sin = ["Activo", "ANTI", "SALPRES", "AP", "MORA12"]
            for col in vars_sin:
                if col not in df_sin.columns: df_sin[col] = 0
            df_sin["Calif.modelo"] = lgbm_sin.predict(df_sin[vars_sin]).astype(str)
            df_sin["Calif.modelo"] = df_sin["Calif.modelo"].map({'0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E'})
            condiciones = [(df_sin["Calif.modelo"] == "A"), (df_sin["Calif.modelo"] == "B") & (df_sin["MORA12"] <= 30), (df_sin["Calif.modelo"] == "B") & (df_sin["MORA12"] > 30) & (df_sin["MORA12"] < 90), (df_sin["Calif.modelo"] == "C") & (df_sin["MORA12"] <= 30), (df_sin["Calif.modelo"] == "C") & (df_sin["MORA12"] > 30) & (df_sin["MORA12"] < 90), (df_sin["Calif.modelo"].isin(["D", "E"])), (df_sin["MORA12"].between(90, 180))]
            df_sin["Calif.homologada"] = np.select(condiciones, ["A", "A", "B", "B", "C", "C", "D"], default="E")

        df_peor_calificacion = pd.concat([df_con[["NIT", "Calif.homologada"]], df_sin[["NIT", "Calif.homologada"]]])
        if not df_peor_calificacion.empty:
            df_peor_calificacion = df_peor_calificacion.groupby("NIT")["Calif.homologada"].max().reset_index()
            mapa_pi_con = {"A": 0.005, "B": 0.006, "C": 0.0441, "D": 0.0448, "E": 0.2273}
            mapa_pi_sin = {"A": 0.015, "B": 0.0595, "C": 0.1382, "D": 0.3277, "E": 0.4171}
            if not df_con.empty:
                df_con["Calif.final"] = df_con["NIT"].map(df_peor_calificacion.set_index("NIT")["Calif.homologada"])
                df_con["PI"] = df_con["Calif.final"].map(mapa_pi_con).astype(float)
                df_con["PE"] = df_con["PI"] * df_con["VEA"] * df_con["PDI"]
            if not df_sin.empty:
                df_sin["Calif.final"] = df_sin["NIT"].map(df_peor_calificacion.set_index("NIT")["Calif.homologada"])
                df_sin["PI"] = df_sin["Calif.final"].map(mapa_pi_sin).astype(float)
                df_sin["PE"] = df_sin["PI"] * df_sin["VEA"] * df_sin["PDI"]

        log_func("Guardando resultados...", "process")

        os.makedirs(carpeta_salida, exist_ok=True)
        log_func(f"Guardando en: {carpeta_salida}", "process")
        ruta_con = os.path.join(carpeta_salida, "PE_con_libranza.xlsx")
        ruta_sin = os.path.join(carpeta_salida, "PE_sin_libranza.xlsx")

        out_files = {}
        if not df_con.empty:
            log_func(f"Guardando: {ruta_con}", "process")
            df_con.to_excel(ruta_con, index=False)
            log_func(f"Guardado: {ruta_con}", "success")
            out_files["con_libranza"] = ruta_con
        if not df_sin.empty:
            log_func(f"Guardando: {ruta_sin}", "process")
            df_sin.to_excel(ruta_sin, index=False)
            log_func(f"Guardado: {ruta_sin}", "success")
            out_files["sin_libranza"] = ruta_sin

        log_func("¡PROCESO FINALIZADO CON ÉXITO!", "success")
        return {"status": "success", "message": "Proceso finalizado con éxito.", "files": out_files}

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        log_func(f"ERROR CRÍTICO: {str(e)}\n{trace}", "error")
        return {"status": "error", "message": f"Ocurrió un error crítico: {e}\n\nDetalles:\n{trace}"}
