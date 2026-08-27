from django.contrib.admin import AdminSite
from django.contrib import admin


class AdminSiteSeguro(AdminSite):
    """
    Panel de administración restringido a superusuarios.
    ISO 27001 A.9.2 — Gestión de acceso de usuarios privilegiados.

    Un usuario con is_staff=True pero is_superuser=False
    verá un error 403 en lugar del panel.
    """
    site_header = 'Administración — Mi Proyecto'
    site_title = 'Admin'
    index_title = 'Panel de control'

    def has_permission(self, request):
        # Solo superusuarios activos pueden entrar
        return request.user.is_active and request.user.is_superuser


# Instancia del admin seguro — reemplaza el admin por defecto
admin_site = AdminSiteSeguro(name='admin')
