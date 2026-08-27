from django.urls import path
from . import views

app_name = 'consultas'

urlpatterns = [
    # Médico
    path('mis-citas/',                              views.citas_medico,              name='citas_medico'),
    path('buscar/',                                 views.buscar_paciente,           name='buscar_paciente'),
    path('paciente/<int:paciente_id>/',             views.historial_paciente,        name='historial_paciente'),
    path('registrar/<int:cita_id>/',                views.registrar_consulta,        name='registrar'),
    path('<int:consulta_id>/',                      views.detalle_consulta,          name='detalle'),
    path('<int:consulta_id>/editar/',               views.editar_consulta,           name='editar'),
    path('<int:consulta_id>/imprimir/',             views.imprimir_consulta,         name='imprimir'),
    path('<int:consulta_id>/diagnostico/',          views.agregar_diagnostico,       name='agregar_diagnostico'),
    path('<int:consulta_id>/prescripcion/',         views.agregar_prescripcion,      name='agregar_prescripcion'),
    path('diagnostico/<int:diag_id>/eliminar/',     views.eliminar_diagnostico,      name='eliminar_diagnostico'),
    path('prescripcion/<int:presc_id>/eliminar/',   views.eliminar_prescripcion,     name='eliminar_prescripcion'),
    # Paciente
    path('historial/<int:consulta_id>/',            views.detalle_consulta_paciente, name='detalle_paciente'),
    path('historial/<int:consulta_id>/imprimir/',   views.imprimir_consulta,         name='imprimir_paciente'),
]
