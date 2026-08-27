from django.contrib.admin import ModelAdmin, TabularInline
from mi_proyecto.admin_site import admin_site
from .models import Consulta, Diagnostico, Prescripcion


class DiagnosticoInline(TabularInline):
    model = Diagnostico
    extra = 1
    fields = ['codigo_cie10', 'descripcion']


class PrescripcionInline(TabularInline):
    model = Prescripcion
    extra = 1
    fields = ['medicamento', 'dosis', 'indicaciones']


class ConsultaAdmin(ModelAdmin):
    list_display = ['pk', 'cita', 'fecha_consulta', 'creado_en']
    search_fields = ['cita__paciente__nombre', 'cita__medico__nombre']
    date_hierarchy = 'fecha_consulta'
    inlines = [DiagnosticoInline, PrescripcionInline]


admin_site.register(Consulta, ConsultaAdmin)
