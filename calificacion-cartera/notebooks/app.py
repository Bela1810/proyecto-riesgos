import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Estimador de PE", layout="wide")

st.title("Estimador de Pérdida Esperada (PE)")
st.markdown("""
Esta aplicación permite estimar la Pérdida Esperada (PE) procesando los archivos de cartera y asociados, 
y aplicando los modelos de Machine Learning entrenados.
""")

# --- Entradas de Usuario ---
# --- Entradas de Usuario (Configuración) ---
import tkinter as tk
from tkinter import filedialog

# Inicializar variables en session_state si no existen
default_paths = {
    "carpeta_base": r"C:\Users\jhquiza\OneDrive - Universidad de Medellin\2025-2\Proyecto riesgos\Archivos septiembre 2025",
    "carpeta_salida": r"C:\Users\jhquiza\OneDrive - Universidad de Medellin\2025-2\Proyecto riesgos\Archivos septiembre 2025"
}

for key, val in default_paths.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Funciones para selección de archivos/carpetas
def seleccionar_carpeta(key):
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    folder_path = filedialog.askdirectory(master=root)
    root.destroy()
    if folder_path:
        st.session_state[key] = folder_path
        st.rerun()

# Determinar el decorador de diálogo disponible
if hasattr(st, 'dialog'):
    dialog_decorator = st.dialog
elif hasattr(st, 'experimental_dialog'):
    dialog_decorator = st.experimental_dialog
else:
    dialog_decorator = None

if dialog_decorator:
    @dialog_decorator("Configuración de Rutas")
    def configurar_rutas():
        st.write("Seleccione las carpetas de trabajo:")
        
        # Carpeta Base (Entrada)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input("Carpeta de Archivos (Entrada)", value=st.session_state["carpeta_base"], disabled=True)
        with col2:
            if st.button("📂 Buscar", key="btn_base"):
                seleccionar_carpeta("carpeta_base")

        # Carpeta Salida
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input("Carpeta Salida", value=st.session_state["carpeta_salida"], disabled=True)
        with col2:
            if st.button("📂 Buscar", key="btn_salida"):
                seleccionar_carpeta("carpeta_salida")
        
        if st.button("Cerrar", type="primary"):
            st.session_state.dialog_open = False
            st.rerun()

    if "dialog_open" not in st.session_state:
        st.session_state.dialog_open = False

    if st.button("⚙️ Configurar Rutas"):
        st.session_state.dialog_open = True
        st.rerun()

    if st.session_state.dialog_open:
        configurar_rutas()

else:
    st.warning("Tu versión de Streamlit no soporta diálogos. Se usarán los valores por defecto o configurados previamente.")

# Asignar variables para uso en el resto del script
carpeta_base = st.session_state["carpeta_base"]
carpeta_salida = st.session_state["carpeta_salida"]

# Asignar variables para uso en el resto del script
carpeta_creditos = st.session_state["carpeta_creditos"]
archivo_asociados = st.session_state["archivo_asociados"]
modelo_con_path = st.session_state["modelo_con_path"]
modelo_sin_path = st.session_state["modelo_sin_path"]
carpeta_salida = st.session_state["carpeta_salida"]

# --- Funciones Auxiliares ---

meses_es = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

def mes_ano_to_date(mes_ano):
    try:
        mes, ano = mes_ano.split('_')
        return pd.Timestamp(year=int(ano), month=meses_es[mes], day=1)
    except Exception as e:
        st.error(f"Error al convertir fecha del archivo: {mes_ano}. Error: {e}")
        return None

def calcular_pdi(row):
    clase = row['clasegarantia']
    morosidad = row['Morosidad']
    
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

def procesar_datos():
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    try:
        # 1. Descubrimiento de Archivos
        status_text.text("Buscando archivos en la carpeta base...")
        if not os.path.exists(carpeta_base):
            st.error(f"La carpeta base no existe: {carpeta_base}")
            return

        archivos_en_base = os.listdir(carpeta_base)
        
        # Identificar archivos por palabras clave
        archivos_credito = [f for f in archivos_en_base if "CREDITO" in f.upper() and f.endswith('.xlsx')]
        archivo_asociados = next((f for f in archivos_en_base if "ASOCIADOS" in f.upper() and f.endswith('.xlsx')), None)
        archivo_aportes = next((f for f in archivos_en_base if "APORTES" in f.upper() and f.endswith('.xlsx')), None)
        archivo_captaciones = next((f for f in archivos_en_base if "CAPTACIONES" in f.upper() and f.endswith('.xlsx')), None)
        
        # Identificar modelos (asumiendo nombres distintivos o palabras clave adicionales si es necesario)
        # Se busca por extensión .joblib y palabras clave "con" o "sin"
        modelo_con_path = next((os.path.join(carpeta_base, f) for f in archivos_en_base if f.endswith('.joblib') and "con" in f.lower()), None)
        modelo_sin_path = next((os.path.join(carpeta_base, f) for f in archivos_en_base if f.endswith('.joblib') and "sin" in f.lower()), None)

        if not archivos_credito:
            st.error("No se encontraron archivos de CRÉDITO en la carpeta base.")
            return
        if not archivo_asociados:
            st.error("No se encontró el archivo de ASOCIADOS en la carpeta base.")
            return
        if not archivo_aportes:
            st.warning("No se encontró el archivo de APORTES. Se asumirá AP=0.")
        if not archivo_captaciones:
            st.warning("No se encontró el archivo de CAPTACIONES. Se asumirá COOCDAT=0.")
        if not modelo_con_path or not modelo_sin_path:
            st.error("No se encontraron los modelos (.joblib) 'con' y 'sin' libranza en la carpeta base.")
            return

        # 2. Cargar y Procesar Archivos de Crédito
        status_text.text("Procesando archivos de crédito...")
        dataframes = {}
        total_archivos = len(archivos_credito)
        
        for i, archivo in enumerate(archivos_credito):
            try:
                nombre_df = archivo.split('.')[0]
                # Intentar extraer MES_ANO si el formato es consistente, sino usar nombre completo
                if '_' in nombre_df:
                    parts = nombre_df.split('_')
                    # Buscar partes que parezcan mes y año
                    # Estrategia simple: tomar las dos últimas partes si son mes y año, o usar split como antes
                    # Asumiendo formato similar al anterior: PREFIJO_MES_ANO
                    if len(parts) >= 3:
                        nombre_df = f"{parts[-2]}_{parts[-1]}"
                    elif len(parts) == 2:
                        nombre_df = parts[1] # Caso MES_ANO directo
                
                ruta_archivo = os.path.join(carpeta_base, archivo)
                
                # Leer archivo
                df_temp = pd.read_excel(ruta_archivo, header=3)
                
                # Preprocesamiento básico por archivo
                cols_req = ['NIT', 'NroCredito', 'CodigoContable', 'Morosidad','ValorPrestamo', 'SaldoCapital', 'SaldoIntereses', 'OtrosSaldos', 'clasegarantia']
                # Verificar columnas
                missing_cols = [c for c in cols_req if c not in df_temp.columns]
                if missing_cols:
                    st.warning(f"Archivo {archivo} ignora columnas faltantes: {missing_cols}")
                    continue

                df_temp = df_temp[cols_req]
                df_temp = df_temp.dropna(subset=['NroCredito'])
                df_temp = df_temp.drop_duplicates(subset=['NroCredito'])
                df_temp = df_temp.set_index('NroCredito')
                df_temp['SALPRES'] = df_temp['SaldoCapital']/df_temp['ValorPrestamo']
                df_temp['VEA'] = df_temp['SaldoCapital']+df_temp['SaldoIntereses']+df_temp['OtrosSaldos']
                
                dataframes[nombre_df] = df_temp
                progress_bar.progress((i + 1) / total_archivos * 0.2)
            except Exception as e:
                st.warning(f"No se pudo procesar el archivo de crédito {archivo}: {e}")

        if not dataframes:
            st.error("No se cargaron dataframes de crédito válidos.")
            return

        # 3. Ordenar y Fusionar Dataframes (Lógica Histórica)
        status_text.text("Fusionando datos históricos de crédito...")
        try:
            meses_ordenados = sorted(dataframes.keys(), key=mes_ano_to_date)
        except Exception as e:
            st.error(f"Error al ordenar archivos por fecha. Asegúrese que los nombres contengan MES_ANO (ej. ENERO_2025). Error: {e}")
            return
        
        if not meses_ordenados:
             st.error("No se pudieron ordenar los meses.")
             return

        # Inicializar con el primer mes
        df_mora = dataframes[meses_ordenados[0]][['NIT', 'Morosidad', 'CodigoContable', 'SALPRES', 'VEA']].copy()
        df_mora = df_mora.rename(columns={
            'Morosidad': f'Morosidad_{meses_ordenados[0]}', 
            'CodigoContable': f'CodigoContable_{meses_ordenados[0]}', 
            'NIT': f'NIT_{meses_ordenados[0]}',
            'SALPRES': f'SALPRES_{meses_ordenados[0]}',
            'VEA': f'VEA_{meses_ordenados[0]}',
            'clasegarantia': f'clasegarantia_{meses_ordenados[0]}'
        })

        # Merge con el resto de meses
        for i, mes in enumerate(meses_ordenados[1:]):
            df_temp = dataframes[mes][['NIT', 'Morosidad', 'CodigoContable', 'SALPRES', 'VEA', 'clasegarantia']].copy()
            df_temp = df_temp.rename(columns={
                'Morosidad': f'Morosidad_{mes}', 
                'CodigoContable': f'CodigoContable_{mes}', 
                'NIT': f'NIT_{mes}',
                'SALPRES': f'SALPRES_{mes}',
                'VEA': f'VEA_{mes}',
                'clasegarantia': f'clasegarantia_{mes}'
            })
            df_mora = df_mora.merge(df_temp, left_index=True, right_index=True, how='outer')
            progress_bar.progress(0.2 + (i + 1) / len(meses_ordenados[1:]) * 0.2)

        # 4. Filtrar y Calcular Variables Derivadas (MORA12, PDI)
        status_text.text("Calculando variables derivadas (MORA12, PDI)...")
        last_month = meses_ordenados[-1]
        df_mora = df_mora.dropna(subset=[f'NIT_{last_month}'])
        
        # Calcular MORA12
        df_mora[f'MORA12_{last_month}'] = df_mora.filter(like='Morosidad').max(axis=1, skipna=True)
        
        # Renombrar columnas finales
        new_column_names = {
            f'Morosidad_{last_month}': 'Morosidad',
            f'CodigoContable_{last_month}': 'CodigoContable',
            f'NIT_{last_month}': 'NIT',
            f'SALPRES_{last_month}': 'SALPRES',
            f'VEA_{last_month}': 'VEA',
            f'MORA12_{last_month}': 'MORA12',
            f'clasegarantia_{last_month}': 'clasegarantia'
        }
        
        columnas_a_conservar = list(new_column_names.keys())
        df_mora = df_mora[columnas_a_conservar].rename(columns=new_column_names)
        df_mora = df_mora.reset_index()
        
        # Calcular SINMORA y PDI
        df_mora['SINMORA'] = np.where(df_mora['MORA12'] == 0, 1, 0)
        df_mora['PDI'] = df_mora.apply(calcular_pdi, axis=1)
        
        progress_bar.progress(0.5)

        # 5. Procesar Informe de Asociados (ANTI)
        status_text.text("Procesando informe de asociados (ANTI)...")
        ruta_asociados = os.path.join(carpeta_base, archivo_asociados)
        
        # Extraer mes/año del nombre
        try:
            nombre_clean = archivo_asociados.split('.')[0]
            # Buscar patrón MES_ANO
            parts = nombre_clean.split('_')
            mes_anno_asoc = f"{parts[-2]}_{parts[-1]}" # Heurística
        except:
            mes_anno_asoc = last_month # Fallback al último mes de crédito

        df_asociados = pd.read_excel(ruta_asociados, header=3)
        df_asociados['Fecha de ingreso'] = pd.to_datetime(df_asociados['Fecha de ingreso'], errors='coerce', format='%d/%m/%Y')
        df_asociados['Activo'] = df_asociados['Activo'].fillna(1).astype(int)
        
        try:
            ultimo_dia_mes = mes_ano_to_date(mes_anno_asoc) + pd.offsets.MonthEnd(0)
        except:
             ultimo_dia_mes = mes_ano_to_date(last_month) + pd.offsets.MonthEnd(0)

        df_asociados['ANTI'] = df_asociados['Activo'] * (ultimo_dia_mes - df_asociados['Fecha de ingreso']).dt.days
        
        # Merge Asociados
        df_mora['NIT'] = df_mora['NIT'].astype(str)
        df_asociados['Número de identificación'] = df_asociados['Número de identificación'].astype(str)
        
        df_features = pd.merge(
            df_mora,
            df_asociados[['Número de identificación', 'Activo', 'ANTI']],
            left_on='NIT',
            right_on='Número de identificación',
            how='left'
        )
        df_features = df_features.drop(columns=['Número de identificación'])
        progress_bar.progress(0.6)

        # 6. Procesar Informe de Aportes (AP)
        status_text.text("Procesando informe de aportes (AP)...")
        if archivo_aportes:
            ruta_aportes = os.path.join(carpeta_base, archivo_aportes)
            df_aportes = pd.read_excel(ruta_aportes, header=3)
            df_aportes['Aporte/Contribución Ordinario'] = df_aportes['Aporte/Contribución Ordinario'].fillna(0)
            df_aportes = df_aportes.rename(columns={'Aporte/Contribución Ordinario': 'AP'})
            df_aportes['Número de identificación'] = df_aportes['Número de identificación'].astype(str)
            
            df_features = pd.merge(
                df_features,
                df_aportes[['Número de identificación', 'AP']],
                left_on='NIT',
                right_on='Número de identificación',
                how='left'
            )
            df_features = df_features.drop(columns=['Número de identificación'])
        else:
            df_features['AP'] = 0

        progress_bar.progress(0.7)

        # 7. Procesar Informe de Captaciones (COOCDAT)
        status_text.text("Procesando informe de captaciones (COOCDAT)...")
        if archivo_captaciones:
            ruta_captaciones = os.path.join(carpeta_base, archivo_captaciones)
            df_captaciones = pd.read_excel(ruta_captaciones, header=3)
            
            df_captaciones['es CDAT'] = df_captaciones['NombreDeposito'].str.contains('CDAT', case=False, na=False).astype(int)
            df_captaciones['COOCDAT'] = df_captaciones['es CDAT'] * df_captaciones['Saldo']
            df_captaciones = df_captaciones[df_captaciones['es CDAT']==1]
            df_captaciones = df_captaciones[['NIT', 'COOCDAT']]
            
            # Agrupar por NIT
            df_captaciones['NIT'] = df_captaciones['NIT'].astype(str)
            df_captaciones = df_captaciones.groupby('NIT').sum().reset_index()
            
            df_features = pd.merge(
                df_features,
                df_captaciones,
                on='NIT',
                how='left'
            )
        else:
            df_features['COOCDAT'] = 0
            
        progress_bar.progress(0.8)

        # 8. Cargar Modelos y Predecir
        status_text.text("Ejecutando modelos de predicción...")
        
        lgbm_con = joblib.load(modelo_con_path)
        lgbm_sin = joblib.load(modelo_sin_path)
        
        cod_con_libranza = [141105, 141110, 141115, 141120, 144105, 144110, 144115, 144120, 144125]
        
        # Separar DataFrames
        df_con = df_features[df_features['CodigoContable'].isin(cod_con_libranza)].copy()
        df_sin = df_features[~df_features['CodigoContable'].isin(cod_con_libranza)].copy()
        
        # --- Predicción Con Libranza ---
        if not df_con.empty:
            df_con['COOCDAT'] = df_con['COOCDAT'].fillna(0)
            df_con = df_con[df_con['Activo'] == 1]
            df_con['AP'] = df_con['AP'].fillna(0)
            
            vars_con = ['AP', 'COOCDAT', 'MORA12', 'SINMORA', 'ANTI']
            # Asegurar columnas
            for col in vars_con:
                if col not in df_con.columns:
                    df_con[col] = 0
            
            # Predecir Z (raw score) si el modelo lo soporta, o classes
            # El notebook usa predict para obtener Z? No, el notebook usa predict para obtener Z directamente? 
            # Revisando notebook: lgbm.predict(X) devuelve valores continuos o clases?
            # En el notebook: df['Z'] = model.predict(X). 
            # Si es LGBMClassifier, predict devuelve clases. Si es LGBMRegressor, devuelve valor.
            # El código anterior usaba predict y luego mapeaba 0,1,2,3 a A,B,C,D.
            # El notebook NUEVO usa sigmoide sobre Z. Esto sugiere que el modelo devuelve raw scores o es una regresión/clasificación binaria?
            # Si el modelo anterior devolvía 0,1,2,3, era clasificación multiclase.
            # El usuario dice "tal como se hace en el notebook".
            # En el notebook: df['Z'] = model.predict(...) -> df['Puntaje'] = 1/(1+exp(-Z)).
            # Esto implica que model.predict devuelve un logit (raw score).
            # Asumiremos que los modelos .joblib cargados ahora se comportan como en el notebook.
            
            try:
                df_con['Calif.modelo'] = lgbm_con.predict(df_con[vars_con])
                df_con['Calif.modelo'] = df_con['Calif.modelo'].map({0: 'A', 1: 'B', 2: 'C', 3:'D', 4:'E'})

                condiciones = [
                    (df_con['Calif.modelo'] == 'A'),
                    (df_con['Calif.modelo'] == 'B') & (df_con['MORA12'] <= 30),
                    (df_con['Calif.modelo'] == 'B') & (df_con['MORA12'] > 30) & (df_con['MORA12'] < 90),
                    (df_con['Calif.modelo'] == 'C') & (df_con['MORA12'] <= 30),
                    (df_con['Calif.modelo'] == 'C') & (df_con['MORA12'] > 30) & (df_con['MORA12'] < 90),
                    (df_con['Calif.modelo'].isin(['D', 'E'])),
                    (df_con['MORA12'].between(90, 180))
                ]

                opciones = ['A', 'A', 'B', 'B', 'C', 'C', 'D']

                df_con['Calif.homologada'] = np.select(condiciones, opciones, default='E')
            except Exception as e:
                st.warning(f"Error en predicción Con Libranza (posible incompatibilidad de modelo): {e}")
            
                         
        # --- Predicción Sin Libranza ---
        if not df_sin.empty:
            df_sin[['Activo', 'ANTI', 'AP']] = df_sin[['Activo', 'ANTI', 'AP']].fillna(0)
            vars_sin = ['Activo', 'ANTI', 'SALPRES', 'AP', 'MORA12']
            
            for col in vars_sin:
                if col not in df_sin.columns:
                    df_sin[col] = 0
            
            try:
                df_sin['Calif.modelo'] = lgbm_sin.predict(df_sin[vars_sin])
                df_sin['Calif.modelo'] = df_sin['Calif.modelo'].map({0: 'A', 1: 'B', 2: 'C', 3:'D', 4:'E'})
                
                condiciones = [
                    (df_sin['Calif.modelo'] == 'A'),
                    (df_sin['Calif.modelo'] == 'B') & (df_sin['MORA12'] <= 30),
                    (df_sin['Calif.modelo'] == 'B') & (df_sin['MORA12'] > 30) & (df_sin['MORA12'] < 90),
                    (df_sin['Calif.modelo'] == 'C') & (df_sin['MORA12'] <= 30),
                    (df_sin['Calif.modelo'] == 'C') & (df_sin['MORA12'] > 30) & (df_sin['MORA12'] < 90),
                    (df_sin['Calif.modelo'].isin(['D', 'E'])),
                    (df_sin['MORA12'].between(90, 180))
                ]

                opciones = ['A', 'A', 'B', 'B', 'C', 'C', 'D']

                df_sin['Calif.homologada'] = np.select(condiciones, opciones, default='E')
                
            except Exception as e:
                st.warning(f"Error en predicción Sin Libranza: {e}")

            # Calcular PI y PE
            df_peor_calificacion = pd.concat([df_con[['NIT', 'Calif.homologada']], df_sin[['NIT', 'Calif.homologada']]])
            df_peor_calificacion = df_peor_calificacion.groupby('NIT')['Calif.homologada'].max().reset_index()
            #df_peor_calificacion = df_peor_calificacion.rename(columns={'Calif.homologada': 'Calif.final'}) 

            df_con['Calif.final'] = df_con['NIT'].map(df_peor_calificacion.set_index('NIT')['Calif.homologada'])
            df_sin['Calif.final'] = df_sin['NIT'].map(df_peor_calificacion.set_index('NIT')['Calif.homologada']) 

            df_con['PI'] = df_con['Calif.final'].map({
                'A': 0.005,
                'B': 0.006,
                'C': 0.0441,
                'D': 0.0448,
                'E': 0.2273
            }).astype(float)

            df_con['PE'] = df_con['PI'] * df_con['VEA'] * df_con['PDI']

            df_sin['PI'] = df_sin['Calif.final'].map({
                'A': 0.015,
                'B': 0.0595,
                'C': 0.1382,
                'D': 0.3277,
                'E': 0.4171
            }).astype(float)
            
            df_sin['PE'] = df_sin['PI'] * df_sin['VEA'] * df_sin['PDI']

        progress_bar.progress(0.9)
        
        # 9. Guardar Resultados
        status_text.text("Guardando archivos CSV...")
        
        if not os.path.exists(carpeta_salida):
            os.makedirs(carpeta_salida)
            
        ruta_con = os.path.join(carpeta_salida, 'PE_con_libranza.csv')
        ruta_sin = os.path.join(carpeta_salida, 'PE_sin_libranza.csv')
        
        if not df_con.empty:
            df_con.to_csv(ruta_con, index=False)
            st.success(f"Archivo guardado: {ruta_con}")
            st.dataframe(df_con.head())
        else:
            st.warning("No se generaron datos para 'Con Libranza'.")

        if not df_sin.empty:
            df_sin.to_csv(ruta_sin, index=False)
            st.success(f"Archivo guardado: {ruta_sin}")
            st.dataframe(df_sin.head())
        else:
            st.warning("No se generaron datos para 'Sin Libranza'.")
            
        progress_bar.progress(1.0)
        status_text.text("¡Proceso completado con éxito!")

    except Exception as e:
        st.error(f"Ocurrió un error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

# --- Botón de Ejecución ---
if st.button("Ejecutar Estimación"):
    procesar_datos()
