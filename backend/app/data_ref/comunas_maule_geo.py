"""
Coordenadas geográficas (centroides) de las comunas de la Región del Maule.
============================================================================
Fuente: cartografía pública del Instituto Nacional de Estadísticas (INE) /
División Político-Administrativa (DPA). Latitud/longitud en grados decimales
(WGS84). Se almacenan en `comunas_resumen.lat/lon` para que el frontend
consuma la geolocalización desde la API y no desde datos estáticos.

Clave: código CUT de 5 dígitos. Valor: (lat, lon).
"""

COMUNAS_MAULE_GEO: dict[str, tuple[float, float]] = {
    "07101": (-35.4264, -71.6553),  # Talca
    "07102": (-35.3329, -72.4116),  # Constitución
    "07103": (-35.0901, -72.0231),  # Curepto
    "07104": (-35.5950, -72.2817),  # Empedrado
    "07105": (-35.5167, -71.7167),  # Maule
    "07106": (-35.4500, -71.4667),  # Pelarco
    "07107": (-35.3833, -71.8167),  # Pencahue
    "07108": (-35.2333, -71.2500),  # Río Claro
    "07109": (-35.5333, -71.4833),  # San Clemente
    "07110": (-35.3000, -71.5333),  # San Rafael
    "07201": (-35.9667, -72.3167),  # Cauquenes
    "07202": (-35.7333, -72.5333),  # Chanco
    "07203": (-35.8167, -72.5833),  # Pelluhue
    "07301": (-34.9854, -71.2386),  # Curicó
    "07302": (-34.9750, -71.8094),  # Hualañé
    "07303": (-34.9833, -72.0000),  # Licantén
    "07304": (-35.1167, -71.2833),  # Molina
    "07305": (-34.9333, -71.3667),  # Rauco
    "07306": (-34.9667, -71.1167),  # Romeral
    "07307": (-35.0667, -71.3833),  # Sagrada Familia
    "07308": (-34.8667, -71.1667),  # Teno
    "07309": (-34.8833, -72.0500),  # Vichuquén
    "07401": (-35.8456, -71.5944),  # Linares
    "07402": (-35.7000, -71.4167),  # Colbún
    "07403": (-36.0167, -71.6833),  # Longaví
    "07404": (-36.1444, -71.8264),  # Parral
    "07405": (-36.0500, -71.7667),  # Retiro
    "07406": (-35.5833, -71.7333),  # San Javier
    "07407": (-35.6833, -71.7500),  # Villa Alegre
    "07408": (-35.7833, -71.5833),  # Yerbas Buenas
}
