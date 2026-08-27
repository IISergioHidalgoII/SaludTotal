from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import ModelAdmin
from mi_proyecto.admin_site import admin_site
from .models import Usuario, Especialidad, Paciente, Medico, Administrador


class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'rol', 'is_active', 'date_joined']
    list_filter = ['rol', 'is_active', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol', 'bio')}),
    )


class EspecialidadAdmin(ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


class PacienteAdmin(ModelAdmin):
    list_display = ['nombre', 'rut', 'telefono', 'creado_en']
    search_fields = ['nombre', 'rut']
    raw_id_fields = ['usuario']


class MedicoAdmin(ModelAdmin):
    list_display = ['nombre', 'rut', 'especialidad', 'telefono', 'creado_en']
    list_filter = ['especialidad']
    search_fields = ['nombre', 'rut']
    raw_id_fields = ['usuario']


class AdministradorAdmin(ModelAdmin):
    list_display = ['nombre', 'rut', 'cargo', 'creado_en']
    search_fields = ['nombre', 'rut']
    raw_id_fields = ['usuario']


admin_site.register(Usuario, UsuarioAdmin)
admin_site.register(Especialidad, EspecialidadAdmin)
admin_site.register(Paciente, PacienteAdmin)
admin_site.register(Medico, MedicoAdmin)
admin_site.register(Administrador, AdministradorAdmin)
