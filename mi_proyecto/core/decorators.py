from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def requiere_rol(*roles):
    """
    Decorador de control de acceso por rol — ISO 27001 A.9.4
    ──────────────────────────────────────────────────────────
    Uso:
        @requiere_rol('admin')
        def mi_vista(request): ...

        @requiere_rol('admin', 'medico')
        def otra_vista(request): ...

    Roles disponibles: 'admin', 'medico', 'paciente'
    Los superusuarios siempre tienen acceso.
    """
    def decorador(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorador


def solo_superusuario(view_func):
    """
    Decorador que restringe la vista exclusivamente a superusuarios.

    Uso:
        @solo_superusuario
        def vista_critica(request): ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper
