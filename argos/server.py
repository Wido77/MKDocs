from __future__ import annotations

import json
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .database import Database
from .collectors import collect_passive

PAGE = """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Argos</title><style>body{font-family:system-ui,sans-serif;max-width:880px;margin:3rem auto;padding:0 1rem;background:#f8fafc;color:#172033}main{background:white;padding:2rem;border-radius:12px;box-shadow:0 2px 14px #17203318}form{display:grid;gap:1rem}label{display:grid;gap:.35rem}input,textarea,button{font:inherit;padding:.7rem;border:1px solid #cbd5e1;border-radius:6px}button{background:#1d4ed8;color:white;border:0;cursor:pointer}.check{display:flex;gap:.5rem}.check input{margin-top:.3rem}.item{border-top:1px solid #e2e8f0;padding:1rem 0}small{color:#475569}</style><body><main><h1>Argos</h1><p>Investigación técnica reproducible y local.</p><form id="form"><label>Título<input name="title" required maxlength="200"></label><label>Objetivo (dominio o URL)<input name="target" required maxlength="2048"></label><label>Nota inicial<textarea name="summary" rows="3" maxlength="4000"></textarea></label><label class="check"><input type="checkbox" name="authorized" required><span>Confirmo que el objetivo está dentro de mi alcance autorizado y que esta fase solo guardará investigación pública de bajo impacto.</span></label><button>Crear investigación</button><small id="message"></small></form><h2>Investigaciones</h2><section id="list">Cargando…</section></main><script>const list=document.querySelector('#list'),msg=document.querySelector('#message');const esc=s=>{const d=document.createElement('div');d.textContent=s;return d.innerHTML};async function load(){const r=await fetch('/api/investigations'),x=await r.json();list.innerHTML=x.length?x.map(i=>`<article class=item><strong>${esc(i.title)}</strong><br><small>${esc(i.targets)} · ${new Date(i.created_at).toLocaleString()}</small><p>${esc(i.summary||'Sin nota inicial.')}</p></article>`).join(''):'Aún no hay investigaciones.'}document.querySelector('#form').onsubmit=async e=>{e.preventDefault();msg.textContent='Guardando…';const f=new FormData(e.target),r=await fetch('/api/investigations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:f.get('title'),target:f.get('target'),summary:f.get('summary'),authorized:f.get('authorized')==='on'})}),x=await r.json();if(!r.ok){msg.textContent=x.error;return}e.target.reset();msg.textContent='Investigación creada.';load()};load()</script></body></html>"""


def detail_page(detail: dict[str, object]) -> str:
    investigation = detail["investigation"]
    runs = "".join(f"<li><a href='/investigations/{investigation['id']}?run={r['id']}'>#{r['id']}</a> · {escape(r['status'])} · {escape(r['collector_name'])} · {escape(r['started_at'] or '')}</li>" for r in detail["runs"])
    recipes = {
        "addresses": ("Resolución inicial del hostname; A y AAAA muestran las direcciones publicadas.", "Resolve-DnsName {host} -Type A; Resolve-DnsName {host} -Type AAAA"),
        "a": ("Resuelve IPv4.", "Resolve-DnsName {host} -Type A"), "aaaa": ("Resuelve IPv6.", "Resolve-DnsName {host} -Type AAAA"),
        "cname": ("Muestra el alias canónico del hostname.", "Resolve-DnsName {host} -Type CNAME"), "txt": ("Muestra registros de texto publicados.", "Resolve-DnsName {host} -Type TXT"),
        "ns_zone": ("Muestra los DNS autoritativos de la zona.", "Resolve-DnsName {zone} -Type NS"), "ns_host": ("Comprueba si el hostname es una zona delegada.", "Resolve-DnsName {host} -Type NS"),
        "mx": ("Muestra los servidores de correo de la zona.", "Resolve-DnsName {zone} -Type MX"),
        "chain": ("Sigue los CNAME y consulta A/AAAA del destino final. Las IPs pueden ser de una capa frontal, no del origen.", "Resolve-DnsName {host} -Type CNAME; Resolve-DnsName <destino-final> -Type A; Resolve-DnsName <destino-final> -Type AAAA"),
        "html": ("Guarda el HTML público que devuelve la URL, sin recorrer rutas adicionales.", "Invoke-WebRequest -Uri {url} -OutFile page.html"),
        "analysis": ("Resume scripts, iframes, metadatos y atributos publicados en el HTML descargado.", "Invoke-WebRequest -Uri {url} -OutFile page.html; Select-String -Path page.html -Pattern '<script|<iframe|data-'"),
        "response": ("Solicita solo las cabeceras HTTP y sigue redirecciones.", "curl.exe -I -L {url}"),
        "certificate": ("Abre TLS y muestra emisor, sujeto, fechas y huella.", "$c=New-Object Net.Sockets.TcpClient('{host}',443); $s=New-Object Net.Security.SslStream($c.GetStream(),$false); $s.AuthenticateAsClient('{host}'); $x=New-Object Security.Cryptography.X509Certificates.X509Certificate2($s.RemoteCertificate); $x | Format-List Subject,Issuer,NotBefore,NotAfter,SerialNumber,Thumbprint"),
    }
    host = detail["targets"][0]["value"].replace("https://", "").replace("http://", "").split("/")[0]
    zone = ".".join(host.split(".")[-2:])
    cards = []
    for item in detail["evidence"]:
        value = escape(json.dumps(json.loads(item["value_json"]), ensure_ascii=False, indent=2))
        artifact = ""
        if item["relative_path"]:
            path = item["relative_path"].replace("\\", "/")
            artifact = f'<p><a href="/artifacts/{escape(path)}">Abrir artefacto</a></p>'
        explanation, command = recipes.get(item["evidence_key"], ("Evidencia recogida por Argos.", item["source_reference"]))
        command = command.format(host=host, zone=zone, url=detail["targets"][0]["value"])
        anchor = f"{item['category']}-{item['evidence_key']}"
        cards.append(f"<article id='{anchor}'><h3>{escape(item['category'])} / {escape(item['evidence_key'])}</h3><p>{escape(explanation)}</p><p><strong>PowerShell:</strong></p><pre>{escape(command)}</pre><p><small>Capturado: {escape(item['observed_at'])}</small></p><pre>{value}</pre>{artifact}</article>")
    evidence = "".join(cards)
    index = "".join(f"<li><a href='#{item['category']}-{item['evidence_key']}'>{escape(item['category'])} / {escape(item['evidence_key'])}</a></li>" for item in detail["evidence"])
    return f"<!doctype html><meta charset='utf-8'><title>{escape(investigation['title'])} — Argos</title><style>body{{font-family:system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem;background:#f8fafc}}main{{background:#fff;padding:2rem;border-radius:12px}}article{{border-top:1px solid #ddd;padding:1rem 0}}pre{{background:#172033;color:#e2e8f0;padding:1rem;overflow:auto}}a{{color:#1d4ed8}}nav{{background:#eef2ff;padding:1rem;border-radius:8px}}</style><main><p><a href='/'>← Investigaciones</a></p><h1>{escape(investigation['title'])}</h1><h2>Índice de ejecuciones</h2><ul>{runs or '<li>Aún no hay ejecuciones.</li>'}</ul><nav><strong>Índice de resultados</strong><ol>{index}</ol></nav><h2>Evidencias de la ejecución #{detail['selected_run']}</h2>{evidence or '<p>Aún no hay evidencias.</p>'}</main>"


class ArgosHandler(BaseHTTPRequestHandler):
    database: Database
    artifacts_dir: object

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, status: HTTPStatus, payload: object) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        if self.path.startswith("/artifacts/"):
            relative = unquote(self.path.removeprefix("/artifacts/")).replace("/", "\\")
            candidate = (Path(self.artifacts_dir) / relative).resolve()
            try:
                candidate.relative_to(Path(self.artifacts_dir).resolve())
            except ValueError:
                self.send_json(HTTPStatus.FORBIDDEN, {"error": "Ruta no permitida."})
                return
            if not candidate.is_file():
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Artefacto no encontrado."})
                return
            content = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            mime = "text/plain; charset=utf-8" if candidate.suffix.lower() in {".html", ".json", ".pem"} else "application/octet-stream"
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if self.path.startswith("/investigations/"):
            try:
                parsed = urlsplit(self.path)
                requested_run = parse_qs(parsed.query).get("run", [None])[0]
                detail = self.database.investigation_detail(int(parsed.path.rsplit("/", 1)[1]), int(requested_run) if requested_run else None)
            except ValueError:
                detail = None
            if not detail:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Investigación no encontrada."})
                return
            content = detail_page(detail).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if self.path.startswith("/api/investigations/"):
            try:
                parsed = urlsplit(self.path)
                requested_run = parse_qs(parsed.query).get("run", [None])[0]
                detail = self.database.investigation_detail(int(parsed.path.rsplit("/", 1)[1]), int(requested_run) if requested_run else None)
            except ValueError:
                detail = None
            self.send_json(HTTPStatus.OK if detail else HTTPStatus.NOT_FOUND, detail or {"error": "Investigación no encontrada."})
            return
        if self.path == "/api/health":
            self.send_json(HTTPStatus.OK, {"status": "ok"})
        elif self.path == "/api/investigations":
            self.send_json(HTTPStatus.OK, self.database.list_investigations())
        elif self.path == "/":
            content = PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada."})

    def do_POST(self) -> None:
        if self.path.startswith("/api/targets/") and self.path.endswith("/collect"):
            try:
                target_id = int(self.path.split("/")[3])
                self.send_json(HTTPStatus.CREATED, collect_passive(self.database, self.artifacts_dir, target_id))
            except ValueError as error:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        if self.path != "/api/investigations":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 16_384:
                raise ValueError("La solicitud supera el tamaño máximo permitido.")
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            created = self.database.create_investigation(str(data.get("title", "")), str(data.get("summary", "")), str(data.get("target", "")), data.get("authorized") is True)
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        self.send_json(HTTPStatus.CREATED, created)


def make_server(host: str, port: int, database: Database, artifacts_dir=None) -> ThreadingHTTPServer:
    handler = type("ConfiguredArgosHandler", (ArgosHandler,), {"database": database, "artifacts_dir": artifacts_dir})
    return ThreadingHTTPServer((host, port), handler)
