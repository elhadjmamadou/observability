"""
Vues de monitoring : health check enrichi et endpoint Prometheus.

L'endpoint /metrics est restreint aux réseaux internes (Docker, localhost)
pour éviter toute exposition publique des métriques opérationnelles.
"""

from __future__ import annotations

import ipaddress

from django_prometheus.exports import ExportToDjangoView

from django.db import connection
from django.http import HttpResponseForbidden, JsonResponse

# Réseaux autorisés à scraper /metrics (Prometheus interne + localhost)
_ALLOWED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _is_internal(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in _ALLOWED_NETWORKS)
    except ValueError:
        return False


def metrics_view(request):
    """Endpoint Prometheus /metrics — accessible depuis les réseaux internes uniquement."""
    ip = _client_ip(request)
    if not _is_internal(ip):
        return HttpResponseForbidden(
            "Metrics endpoint restricted to internal networks.",
            content_type="text/plain",
        )
    return ExportToDjangoView(request)


def health_view(request):
    """Health check enrichi : vérifie DB + état général."""
    checks: dict[str, str] = {}
    ok = True

    # Database
    try:
        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        ok = False

    payload = {"status": "ok" if ok else "degraded", "checks": checks}
    status_code = 200 if ok else 503
    return JsonResponse(payload, status=status_code)
