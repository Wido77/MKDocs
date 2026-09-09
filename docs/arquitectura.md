# Arquitectura de Argos

## Decisión

Argos será una aplicación local de escritorio servida en `localhost`. Tendrá una interfaz web sencilla, una API local y una base SQLite por defecto. No requerirá una cuenta, un servicio remoto ni publicar investigaciones para funcionar.

La primera versión prioriza investigaciones reproducibles: una ejecución guarda qué se consultó, cuándo, con qué configuración y qué respuesta pública se obtuvo.

## Componentes

```text
Interfaz local
    ↓
API y orquestador de ejecuciones
    ├── Política de alcance y autorización
    ├── Recolectores pasivos
    │   ├── DNS
    │   ├── HTTP y TLS
    │   └── HTML y recursos publicados
    ├── Normalizador y clasificador de evidencia
    └── Exportador Markdown para MkDocs
    ↓
SQLite + almacén local de artefactos
```

Los recolectores no interpretan una respuesta como una conclusión. Devuelven observaciones normalizadas; las reglas pueden sugerir una inferencia y el usuario revisa el resultado antes de exportarlo.

## Modelo de datos inicial

### Investigación

Representa un asunto de trabajo y uno o varios objetivos. Almacena título, objetivo principal, etiquetas, estado, fecha de creación y una declaración de alcance/autorización.

### Objetivo

Representa un dominio o URL dentro de una investigación. Conserva la URL normalizada, el dominio registrable, el tipo de autorización indicado y notas de alcance.

### Ejecución

Es una captura fechada e inmutable de una recolección. Almacena inicio, fin, versión del recolector, configuración efectiva, estado y posibles errores. Una investigación puede tener muchas ejecuciones para poder comparar cambios.

### Evidencia

Es un hecho observable producido por una ejecución: un CNAME, una cabecera HTTP, un campo del certificado, un `iframe` o un JSON visible en el cliente. Cada elemento incluye:

- categoría y clave normalizadas;
- valor estructurado en JSON;
- fuente y petición que lo produjo;
- marca temporal;
- referencia al artefacto bruto;
- clasificación `evidencia`, `inferencia` o `hipótesis`;
- confianza y nota de interpretación.

### Artefacto

Guarda el contenido bruto necesario para reproducir la evidencia —por ejemplo, una respuesta HTTP, certificado PEM, HTML o HAR— en disco local y registra en SQLite su ruta, hash SHA-256, tamaño, MIME y política de retención.

### Fuente y hallazgo

Una fuente identifica una página, registro público o documento consultado. Un hallazgo enlaza evidencias y fuentes en una afirmación revisable. El hallazgo nunca sustituye los datos de origen.

## Límites técnicos del MVP

- Las solicitudes se ejecutan con tiempo máximo, tamaño máximo de respuesta, redirecciones limitadas y un agente de usuario identificable.
- El formulario exige confirmar el alcance antes de iniciar una ejecución.
- El MVP no incluye autenticación contra objetivos, descubrimiento activo de rutas/hosts, escaneo de puertos ni acciones de escritura.
- Los resultados se almacenan localmente y no se transmiten a terceros desde Argos.
- Las credenciales, tokens y cookies se ocultan en la interfaz y se excluyen de exportaciones por defecto.

## Interfaces previstas

- Crear investigación y añadir objetivos.
- Ejecutar recolección pasiva sobre un objetivo.
- Ver evidencias agrupadas por DNS, TLS, HTTP y contenido público.
- Añadir una nota, fuente o corrección humana a un hallazgo.
- Comparar dos ejecuciones del mismo objetivo.
- Exportar una investigación revisada a `docs/temas/` en Markdown compatible con MkDocs.

La captura de Network/HAR llegará después del MVP mediante un navegador controlado y sin sesión autenticada. Sus solicitudes y respuestas se almacenarán como artefactos y conservarán el mismo modelo de evidencia.

## Paquetes candidatos para la siguiente tarea

- FastAPI y Uvicorn: API e interfaz local.
- SQLModel o SQLAlchemy: persistencia SQLite y migraciones.
- HTTPX: solicitudes HTTP con límites explícitos.
- dnspython: tipos de registro DNS.
- BeautifulSoup o selectolax: análisis de HTML publicado.
- Playwright: navegador y exportación HAR en la fase Network.

La implementación confirmará las versiones y licencias antes de incorporarlas a `requirements.txt`.
