"""
cache.py — Caché en memoria con expiración (TTL) para mejorar el rendimiento
============================================================================
Los endpoints de agregación (resumen nacional, estadísticas) ejecutan JOINs
sobre las tablas hogares/personas/indicadores en cada petición. Como esos
datos son de lectura intensiva y cambian con poca frecuencia, cachear el
resultado durante unos segundos reduce drásticamente la carga de la base de
datos y mejora la latencia bajo concurrencia (S14 · "Mejoras de rendimiento").

Es un caché de proceso, simple y sin dependencias externas. Para un despliegue
multi-instancia se reemplazaría por Redis manteniendo la misma interfaz.
"""

import os
import threading
import time
from typing import Any, Optional

# TTL por defecto (segundos). Configurable por entorno para tests/producción.
DEFAULT_TTL = int(os.getenv("CACHE_TTL_SECONDS", "30"))

_store: dict[str, tuple[float, Any]] = {}
_lock = threading.Lock()


def cache_get(key: str) -> Optional[Any]:
    """Devuelve el valor cacheado si existe y no ha expirado; si no, None."""
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            # Expirado: limpiar y fallar el hit
            _store.pop(key, None)
            return None
        return value


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Almacena un valor con una expiración relativa de `ttl` segundos."""
    with _lock:
        _store[key] = (time.monotonic() + ttl, value)


def clear_cache() -> None:
    """Vacía todo el caché (útil tras cargar datos o en tests)."""
    with _lock:
        _store.clear()


def cache_stats() -> dict:
    """Métricas básicas del caché para observabilidad."""
    with _lock:
        now = time.monotonic()
        vigentes = sum(1 for exp, _ in _store.values() if exp > now)
        return {"entradas": len(_store), "vigentes": vigentes}
