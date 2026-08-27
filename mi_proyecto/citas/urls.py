from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    # ── Paciente: reservar ─────────────────────────────────────
    path('reservar/',                          views.reservar_paso1,      name='reservar_paso1'),
    path('reservar/<int:especialidad_id>/',    views.reservar_paso2,      name='reservar_paso2'),
    path('reservar/medico/<int:medico_id>/',   views.reservar_paso3,      name='reservar_paso3'),
    path('confirmar/<int:agenda_id>/',         views.reservar_confirmar,  name='reservar_confirmar'),
    path('mis-citas/',                         views.mis_citas,           name='mis_citas'),
    path('cancelar/<int:cita_id>/',            views.cancelar_cita,          name='cancelar_cita'),
    # ── Médico: confirmar / rechazar solicitudes ───────────────
    path('accion/confirmar/<int:cita_id>/',    views.confirmar_cita_medico,  name='confirmar_medico'),
    path('accion/rechazar/<int:cita_id>/',     views.rechazar_cita_medico,   name='rechazar_medico'),
    # ── Médico: agenda ─────────────────────────────────────────
    path('agenda/',                            views.agenda_medico,       name='agenda_medico'),
    path('agenda/agregar/',                    views.agenda_crear,        name='agenda_crear'),
    path('agenda/eliminar/<int:agenda_id>/',   views.agenda_eliminar,     name='agenda_eliminar'),
]
