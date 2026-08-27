from django.contrib.admin import ModelAdmin
from mi_proyecto.admin_site import admin_site
from .models import Sala, Agenda, Cita, Notificacion


class SalaAdmin(ModelAdmin):
    list_display = ['nombre', 'tipo', 'capacidad', 'estado', 'ubicacion']
    list_filter = ['tipo', 'estado']
    search_fields = ['nombre']
    list_editable = ['estado']


class AgendaAdmin(ModelAdmin):
    list_display = ['medico', 'fecha', 'hora_inicio', 'hora_fin', 'sala', 'estado']
    list_filter = ['estado', 'medico__especialidad', 'sala']
    search_fields = ['medico__nombre']
    date_hierarchy = 'fecha'


class CitaAdmin(ModelAdmin):
    list_display = ['pk', 'paciente', 'medico', 'hora', 'estado', 'creado_en']
    list_filter = ['estado', 'medico__especialidad']
    search_fields = ['paciente__nombre', 'medico__nombre']
    date_hierarchy = 'creado_en'
    list_editable = ['estado']


class NotificacionAdmin(ModelAdmin):
    list_display = ['cita', 'tipo', 'estado_envio', 'fecha_envio']
    list_filter = ['tipo', 'estado_envio']


admin_site.register(Sala, SalaAdmin)
admin_site.register(Agenda, AgendaAdmin)
admin_site.register(Cita, CitaAdmin)
admin_site.register(Notificacion, NotificacionAdmin)
