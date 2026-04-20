# Instrucciones para ejecutar el proyecto en desarrollo

Estas instrucciones están dirigidas a las personas que vayan a modificar o correr el programa en local.

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

## Iniciar el servicio de python

La logica que involucra la lectura de documentos y la ejecución de los modelos se encuentra escrita en python. Este archivo se encuentra en calificacion-cartera\src\api.py

```bash
uv run ./calificacion-cartera/src/api.py
```

## Iniciar el servidor de react

En la carpeta App se tiene la aplicación de react que contiene la interfaz grafica de la aplicación y se conecta a la api.py. Inicia el servidor de react ejecutando este comando dentro del directorio App con cualquier gestor de paquetes.

```bash
bun run dev

npm run dev

pnpm run dev
```

## Inicia el compilador de Electron

Ya que la aplicación de react está corriendo como servidor web, electron es la capa que lo ejecuta a nivel de sistema operativo como aplicaión.

```bash
bun run electron

npm run electron

pnpm run electron
```
