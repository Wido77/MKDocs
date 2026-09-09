# Investigaciones

Sitio de notas con [MkDocs Material](https://squidfunk.github.io/mkdocs-material/), publicado en GitHub Pages.

## Argos: aplicación local

Argos guarda investigaciones y objetivos en SQLite local. Esta primera versión no realiza consultas de red: prepara el modelo de evidencia y exige confirmar el alcance autorizado antes de crear una investigación.

```powershell
cd "F:\Programacion\SegundoCerebro\Segundo Cerebro\Investigación\Argos"
python -m argos
```

Abre `http://127.0.0.1:8765`. Los datos se guardan en `.argos/` y no se versionan.

## Arranque local (Windows)

```powershell
cd C:\Users\Wido\source\investigaciones
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
mkdocs serve
```

Abre http://127.0.0.1:8000

## Publicar en GitHub Pages

1. Crea un repositorio vacío llamado `investigaciones` en GitHub.
2. En el repo: **Settings → Pages → Source: GitHub Actions**.
3. Desde esta carpeta:

```powershell
git add .
git commit -m "Sitio inicial de investigaciones"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/investigaciones.git
git push -u origin main
```

La Action construye el sitio en cada push a `main`. La URL será:

`https://TU_USUARIO.github.io/investigaciones/`

## Dónde guardar qué

- Notas: `docs/temas/`
- Comandos reutilizables: `docs/comandos/`
- Capturas: `docs/assets/images/`
- Adjuntos: `docs/archivos/`
