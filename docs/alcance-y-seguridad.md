# Alcance y seguridad del investigador

## Propósito

El investigador convierte datos públicos en investigaciones reproducibles. Automatiza la recogida y el archivado de evidencias; las conclusiones siguen requiriendo revisión humana.

## MVP autorizado

El MVP solo realiza recolección de bajo impacto sobre información pública:

- Resolución DNS y análisis de la cadena de nombres.
- Consultas RDAP/WHOIS y de transparencia de certificados mediante fuentes públicas.
- Una solicitud HTTP `HEAD` o `GET` normal contra la URL indicada, respetando redirecciones, límites de tiempo y tamaño de respuesta.
- Extracción del HTML, cabeceras, certificado TLS, scripts, iframes, JSON y configuraciones que el sitio entrega públicamente al navegador.
- Registro de peticiones y respuestas visibles en una sesión de navegador sin autenticación, cuando el usuario lo solicite.
- Correlación con fuentes públicas de contratación y contexto institucional, siempre con enlace y fecha de consulta.

## Límites deliberados

No se incluyen en el MVP:

- Escaneo de puertos, fuerza bruta, explotación o intentos de eludir autenticación y controles de acceso.
- Acceso a áreas privadas, contenido autenticado, datos personales no necesarios o secretos expuestos.
- Enumeración activa de hosts, rutas o entornos de desarrollo/staging sin autorización expresa del titular.
- Atribuciones sobre personas, ubicaciones físicas o proveedores que no estén respaldadas por evidencia verificable.

Las funciones activas futuras deberán quedar deshabilitadas por defecto y exigir una declaración explícita de autorización y alcance por parte del usuario.

## Criterio de evidencia

Cada hallazgo debe almacenar:

- objetivo, fecha y hora de la ejecución;
- fuente, petición o comando que lo produjo;
- resultado bruto o referencia conservada;
- clasificación: **evidencia**, **inferencia** o **hipótesis**;
- nivel de confianza y explicación breve;
- limitaciones conocidas.

Una cabecera, un registro DNS o un recurso cargado demuestra solo lo que expone públicamente. La aplicación evitará presentar como certeza una conclusión arquitectónica que no pueda verificarse.

## Privacidad y retención

La herramienta minimiza la recolección de datos personales, no incluye credenciales en informes y permite eliminar una ejecución local. Los informes exportados deben revisarse antes de publicarse.
