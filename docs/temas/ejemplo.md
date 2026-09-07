# Ejemplo: entorno local

Fecha: 2026-09-07  
Estado: cerrado

Nota de ejemplo para ver el formato. Puedes borrarla cuando tengas la primera investigación real.

## Pregunta

¿Qué versión de Python hay en esta máquina y cómo previsualizo el sitio?

## Hallazgos

- Python 3.11 sirve para MkDocs.
- `mkdocs serve` abre una vista local con recarga al guardar.

## Comandos

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
mkdocs serve
```

Luego abre http://127.0.0.1:8000

!!! warning "PowerShell y venv"
    Si la política de ejecución bloquea el activate, usa:
    `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Capturas

![Imagen de ejemplo embebida en markdown](../assets/images/ejemplo.png)

## Archivos

Los adjuntos viven en `docs/archivos/` y se enlazan así:

```markdown
[Volcado de notes.txt](../archivos/notes.txt)
```
