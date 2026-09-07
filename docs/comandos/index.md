# Comandos

Cheatsheet corta. Cuando un comando merezca contexto, muévelo a una nota en `temas/`.

## Sitio local

```powershell
.\.venv\Scripts\Activate.ps1
mkdocs serve
```

## Construir sin publicar

```powershell
mkdocs build
```

El HTML queda en `site/` (esa carpeta no se sube a git).

## Añadir una nota

1. Crea `docs/temas/nombre.md`
2. Enlázala en `mkdocs.yml` bajo `nav`
3. Guarda y mira el preview
