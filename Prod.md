# Instrucciones para construir ejecutable

Estas instrucciones están dirigidas a las personas que vayan a distribuir y a construir el programa.

---

## Instalación de dependencias

Configure el entorno con uv (Recomendado)

```bash
# Instalar uv si no lo tiene
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Sincronizar el entorno con el archivo pyproject.toml
uv sync
```

---

## Compilar la logica del back en un ejecutable

Ejecuta este comando **en la raiz del proyecto** o en la carpeta "calificacion-cartera" modificando la ruta del comando removiendola del las direcciones a los archivos.

```bash
pyinstaller --onefile --clean --noconfirm `
  --collect-all flask `
  --collect-all flask_cors `
  --collect-all joblib `
  --collect-all numpy `
  --collect-all pandas `
  --collect-all scipy `
  --collect-all sklearn `
  --collect-all threadpoolctl `
  --collect-all lightgbm `
  --collect-all openpyxl `
  --collect-all python_calamine `
  --hidden-import flask `
  --hidden-import flask_cors `
  --hidden-import joblib `
  --hidden-import numpy `
  --hidden-import pandas `
  --hidden-import scipy `
  --hidden-import sklearn `
  --hidden-import threadpoolctl `
  --hidden-import lightgbm `
  --hidden-import openpyxl `
  --hidden-import python_calamine `
  --add-data ".\calificacion-cartera\src\logic.py;." `
  --add-data ".\calificacion-cartera\models\lightgbm_con_libranza.joblib;." `
  --add-data ".\calificacion-cartera\models\lightgbm_sin_libranza.joblib;." `
  .\calificacion-cartera\src\api.py
```

---

## Mover el archivo ejecutable a la carpeta de la aplicación

El archivo resultante se creará en la carpeta "dist" en el directorio que se ejecutó el comando.

Mueve el archivo api.exe a la ruta App/resources/

---

## Empaquetar el proyecto de React

Ingrese a la carpeta "App"

```bash
cd App
```

Y allí ejecute con su manejador de paquetes de preferencia build

```bash
bun run build

npm run build

pnpm run build
```

## Crea el instalador y ejecutable con Electron

Después de haber empaquetado la aplicación de react se compilará junto con el archivo api.exe que se creó anteriormente con el siguiente comando en la carpeta "App" con cualquier gestor de paquetes que desees.

```bash
bun run dist

npm run dist

pnpm run dist
```

## El resultado...

La carpeta App/dist es todo lo que se necesita compartir para distribuir la aplicación.
