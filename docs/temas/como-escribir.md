# Cómo escribir una nota

Copia este esquema y cambia el nombre del archivo (`mi-tema.md`).

Luego añádelo en `mkdocs.yml` dentro de `nav` → `Temas`.

## Plantilla

````markdown
# Título del tema

Fecha: 2026-09-07
Estado: en curso

## Pregunta
Qué estoy intentando entender.

## Hallazgos
- Punto 1
- Punto 2

## Comandos

```bash
whoami
```

## Capturas

![Descripción breve](../assets/images/nombre.png){ width="700" }

## Archivos
- [Notas en PDF](../archivos/ejemplo.pdf)

## Siguientes pasos
- [ ] Leer X
- [ ] Probar Y
````

## Consejos

!!! warning "Sin `!` no es una imagen"
    `[Whois](foto.png)` es un enlace de texto.
    `![Whois](foto.png)` es la foto embebida.

!!! tip "Capturas"
    Desde una nota en `docs/temas/` la ruta es `../assets/images/tema/foto.png`.
    En Cursor: pega el pantallazo con Ctrl+V, o abre la vista previa con Ctrl+K V para verlas al lado del markdown.
    En la web (`mkdocs serve`) también se ven y se pueden ampliar.

!!! info "Archivos grandes"
    GitHub Pages no es un disco duro. Evita binarios enormes (vídeos, ISOs).
    Para eso usa un repo de datos, Drive u otro almacén y deja aquí el enlace.
