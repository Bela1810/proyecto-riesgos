# Repositorio de proyectos de riesgos de la Universidad de Medellín

Este es el repositorio de los proyectos de investigación en riesgos de la Universidad de Medellín.

---

## Instalación

### 1. Crear su propia copia (Fork)

No trabajará directamente sobre el repositorio del profesor. Cada uno debe tener su copia personal en la nube.

1. Entre al enlace del repositorio de la clase: [https://github.com/jhquiza/proyecto-riesgos](https://github.com/jhquiza/proyecto-riesgos).
2. En la esquina superior derecha, haga clic en el botón **Fork**.
3. Asegúrese de que el "Owner" sea su usuario de GitHub y haga clic en **Create fork**.

### 2. Clonar su Fork localmente

Ahora, descargue **su copia** (no la del profesor) a su computadora.

```bash
git clone https://github.com/SU_USUARIO/proyecto-riesgos
cd proyecto-riesgos
```

Configure el entorno con uv (Recomendado)

```bash
# Instalar uv si no lo tiene
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Sincronizar el entorno con el archivo pyproject.toml
uv sync
```

### 3. Configurar el repositorio del Profesor como "Upstream"

Este paso es vital. Sirve para que, si el profesor añade nuevo material o corrige un ejercicio, usted pueda descargar esos cambios sin borrar su propio progreso.

En su terminal, dentro de la carpeta del proyecto, ejecute:

```bash
# Agregue el repo del profesor como una fuente remota llamada "upstream"
git remote add upstream https://github.com/jhquiza/proyecto-riesgos

# Verifique que ahora tiene dos remotos: origin (el suyo) y upstream (el de la clase)
git remote -v

```

Autor: Jhon Quiza
