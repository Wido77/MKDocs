from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
import socket
import ssl
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .database import Database, utc_now


def _artifact(directory: Path, run_id: int, name: str, content: bytes) -> tuple[str, str, int]:
    path = directory / str(run_id) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return str(path.relative_to(directory)), hashlib.sha256(content).hexdigest(), len(content)


class RedirectTracker(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict[str, object]] = []

    def redirect_request(self, request, file_pointer, status, message, headers, new_url):
        self.chain.append({"status": status, "from": request.full_url, "to": new_url})
        return super().redirect_request(request, file_pointer, status, message, headers, new_url)


class PublicHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.iframes: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.data_attributes: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attributes}
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag == "iframe" and values.get("src"):
            self.iframes.append(values["src"])
        if tag == "meta" and (values.get("name") or values.get("property") or values.get("http-equiv")):
            self.meta.append(values)
        data = {key: value for key, value in values.items() if key.startswith("data-")}
        if data:
            self.data_attributes.append({"tag": tag, **data})


def dns_query(record_type: str, hostname: str) -> dict[str, object]:
    """Consulta pasiva mediante nslookup y conserva su respuesta literal."""
    completed = subprocess.run(["nslookup", f"-type={record_type}", hostname], capture_output=True, text=True, timeout=12, check=False)
    return {"record_type": record_type, "hostname": hostname, "return_code": completed.returncode, "output": completed.stdout.strip(), "error": completed.stderr.strip()}


def cname_target(output: str) -> str | None:
    match = re.search(r"canonical name\s*=\s*([^\s]+)", output, re.IGNORECASE)
    return match.group(1).rstrip(".") if match else None


def certificate_metadata(certificate: dict[str, object], sha256: str, cipher: str) -> dict[str, object]:
    def names(entries: object) -> list[str]:
        return ["=".join(pair) for entry in entries or [] for pair in entry]
    return {
        "subject": names(certificate.get("subject")),
        "issuer": names(certificate.get("issuer")),
        "subject_alt_names": [value for _, value in certificate.get("subjectAltName", [])],
        "not_before": certificate.get("notBefore"),
        "not_after": certificate.get("notAfter"),
        "serial_number": certificate.get("serialNumber"),
        "sha256": sha256,
        "cipher": cipher,
    }


def collect_passive(database: Database, artifacts_dir: Path, target_id: int) -> dict[str, object]:
    target = database.get_target(target_id)
    if not target or not target["authorization_confirmed"]:
        raise ValueError("El objetivo no tiene una confirmación de alcance autorizada.")
    url = target["value"] if "://" in target["value"] else f"https://{target['value']}"
    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError("El objetivo debe ser un dominio o URL válida.")
    run_id, observed = database.begin_run(target_id, "passive-network", "0.1"), utc_now()
    try:
        addresses = sorted({entry[4][0] for entry in socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)})
        payload = {"host": parsed.hostname, "addresses": addresses}
        rel, digest, size = _artifact(artifacts_dir, run_id, "dns-addresses.json", json.dumps(payload, indent=2).encode())
        database.add_evidence(run_id, database.add_artifact(run_id, rel, digest, "application/json", size), "dns", "addresses", payload, f"getaddrinfo:{parsed.hostname}", observed)
        dns_host = parsed.hostname
        zone = ".".join(dns_host.split(".")[-2:])
        for record_type, hostname, label in (("A", dns_host, "a"), ("AAAA", dns_host, "aaaa"), ("CNAME", dns_host, "cname"), ("TXT", dns_host, "txt"), ("NS", zone, "ns_zone"), ("NS", dns_host, "ns_host"), ("MX", zone, "mx")):
            result = dns_query(record_type, hostname)
            raw = json.dumps(result, ensure_ascii=False, indent=2).encode()
            rel, digest, size = _artifact(artifacts_dir, run_id, f"dns-{label}.json", raw)
            database.add_evidence(run_id, database.add_artifact(run_id, rel, digest, "application/json", size), "dns", label, result, f"nslookup -type={record_type} {hostname}", observed)
        chain = [dns_host]
        current = dns_host
        for _ in range(5):
            destination = cname_target(dns_query("CNAME", current)["output"])
            if not destination or destination in chain:
                break
            chain.append(destination)
            current = destination
        final_records = {kind: dns_query(kind, current) for kind in ("A", "AAAA")}
        chain_payload = {"chain": chain, "final_hostname": current, "final_records": final_records, "authoritative_zone": zone}
        rel, digest, size = _artifact(artifacts_dir, run_id, "dns-chain.json", json.dumps(chain_payload, ensure_ascii=False, indent=2).encode())
        database.add_evidence(run_id, database.add_artifact(run_id, rel, digest, "application/json", size), "dns", "chain", chain_payload, f"Resolve-DnsName {dns_host} -Type CNAME; Resolve-DnsName {current} -Type A,AAAA", observed)

        request = Request(url, headers={"User-Agent": "Argos/0.1 local passive research"}, method="HEAD")
        redirects = RedirectTracker()
        try:
            response = build_opener(redirects).open(request, timeout=12)
        except HTTPError as error:
            response = error
        http = {"final_url": response.geturl(), "status": response.status, "redirects": redirects.chain, "headers": {key.lower(): value for key, value in response.headers.items()}}
        rel, digest, size = _artifact(artifacts_dir, run_id, "http-head.json", json.dumps(http, ensure_ascii=False, indent=2).encode())
        database.add_evidence(run_id, database.add_artifact(run_id, rel, digest, "application/json", size), "http", "response", http, f"HEAD:{url}", observed)

        page = build_opener().open(Request(url, headers={"User-Agent": "Argos/0.1 local passive research"}), timeout=12).read(1_048_576)
        parser = PublicHTML()
        parser.feed(page.decode("utf-8", errors="replace"))
        analysis = {"scripts": parser.scripts, "iframes": parser.iframes, "meta": parser.meta, "data_attributes": parser.data_attributes, "content_bytes": len(page)}
        rel, digest, size = _artifact(artifacts_dir, run_id, "page.html", page)
        html_artifact = database.add_artifact(run_id, rel, digest, "text/html", size)
        database.add_evidence(run_id, html_artifact, "content", "html", {"sha256": digest, "byte_size": size}, f"GET:{url}", observed)
        rel, digest, size = _artifact(artifacts_dir, run_id, "content-analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2).encode())
        database.add_evidence(run_id, database.add_artifact(run_id, rel, digest, "application/json", size), "content", "analysis", analysis, f"GET:{url}", observed)

        if parsed.scheme == "https":
            with socket.create_connection((parsed.hostname, parsed.port or 443), timeout=12) as sock:
                with ssl.create_default_context().wrap_socket(sock, server_hostname=parsed.hostname) as tls:
                    certificate = tls.getpeercert()
                    pem = ssl.DER_cert_to_PEM_cert(tls.getpeercert(binary_form=True)).encode()
                    rel, digest, size = _artifact(artifacts_dir, run_id, "certificate.pem", pem)
                    metadata = certificate_metadata(certificate, digest, tls.cipher()[0])
                    database.add_evidence(run_id, database.add_artifact(run_id, rel, digest, "application/x-pem-file", size), "tls", "certificate", metadata, f"TLS:{parsed.hostname}", observed)
        database.finish_run(run_id, "completed")
        return {"run_id": run_id, "status": "completed"}
    except (OSError, ssl.SSLError, URLError, ValueError) as error:
        database.finish_run(run_id, "failed", str(error))
        raise ValueError(f"La recolección no se completó: {error}") from error
