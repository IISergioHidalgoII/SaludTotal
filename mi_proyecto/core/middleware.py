from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


# Rutas que requieren autenticación (prefijos)
RUTAS_PROTEGIDAS = [
    '/dashboard/',
    '/citas/',
    '/consultas/',
    '/reportes/',
    '/usuarios/perfil/',
    # Nota: /usuarios/registro/ y /usuarios/verificar/ son públicas
]

# Rutas que requieren ser superusuario
RUTAS_SOLO_SUPERUSUARIO = [
    '/admin/',
]


class ControlAccesoMiddleware:
    """
    Middleware de control de acceso — ISO 27001 A.9
    ─────────────────────────────────────────────────
    - Bloquea acceso a rutas protegidas si no está autenticado.
    - Bloquea /admin a usuarios que no sean superusuarios.
    - Redirige al login con mensaje en lugar de exponer que la ruta existe.

    Para agregar más rutas protegidas, edita las listas de arriba.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ruta = request.path_info

        # ── 1. /admin solo para superusuarios ─────────────────
        if any(ruta.startswith(p) for p in RUTAS_SOLO_SUPERUSUARIO):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión para continuar.')
                return redirect(f'/usuarios/login/?next={ruta}')
            if not request.user.is_superuser:
                raise PermissionDenied  # → error 403

        # ── 2. Rutas protegidas requieren login ────────────────
        if any(ruta.startswith(p) for p in RUTAS_PROTEGIDAS):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión para acceder a esa página.')
                return redirect(f'/usuarios/login/?next={ruta}')

        return self.get_response(request)
