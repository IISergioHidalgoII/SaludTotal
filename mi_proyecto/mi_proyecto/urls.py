from django.urls import include, path

from .admin_site import admin_site

handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('core.urls', namespace='core')),
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),
    path('citas/', include('citas.urls', namespace='citas')),
    path('consultas/', include('consultas.urls', namespace='consultas')),
]
