from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from citas.models import Cita, Agenda, Sala
from citas.services import _auto_confirmar_pendientes
from usuarios.models import Medico, Especialidad, Paciente


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_csrf(request, reason=''):
    """Vista limpia para fallos CSRF — redirige al inicio con mensaje."""
    messages.warning(
        request,
        'Tu sesión ha expirado o el formulario ya fue enviado. Por favor inténtalo de nuevo.',
    )
    return redirect(request.META.get('HTTP_REFERER', '/'))


def index(request):
    return render(request, 'core/index.html')


@login_required
def dashboard(request):
    context = {}

    if request.user.rol == 'paciente':
        try:
            paciente = request.user.perfil_paciente
            citas_qs = Cita.objects.filter(paciente=paciente).select_related(
                'medico__especialidad', 'agenda'
            ).order_by('-agenda__fecha')
            context['total_citas'] = citas_qs.count()
            context['citas_recientes'] = citas_qs[:5]
        except (AttributeError, Paciente.DoesNotExist):
            context['total_citas'] = 0
            context['citas_recientes'] = []

    elif request.user.rol == 'medico':
        try:
            medico = request.user.perfil_medico
            _auto_confirmar_pendientes(medico)
            citas_qs = Cita.objects.filter(medico=medico).select_related('paciente', 'agenda')
            context['citas_pendientes_count']  = citas_qs.filter(estado='pendiente').count()
            context['citas_confirmadas_count'] = citas_qs.filter(estado='confirmada').count()
            context['citas_realizadas_count']  = citas_qs.filter(estado='realizada').count()
            context['citas_proximas'] = (
                citas_qs.filter(estado='confirmada')
                .order_by('agenda__fecha', 'hora')[:8]
            )
            context['citas_solicitudes'] = (
                citas_qs.filter(estado='pendiente')
                .order_by('agenda__fecha', 'hora')[:5]
            )
        except (AttributeError, Medico.DoesNotExist):
            context['citas_pendientes_count']  = 0
            context['citas_confirmadas_count'] = 0
            context['citas_realizadas_count']  = 0
            context['citas_proximas']   = []
            context['citas_solicitudes'] = []

    return render(request, 'core/dashboard.html', context)


# ══════════════════════════════════════════════════════════════
#  REPORTES — Solo admin
# ══════════════════════════════════════════════════════════════

def _solo_admin(request):
    if not (request.user.es_admin):
        raise PermissionDenied


@login_required
def reporte_general(request):
    _solo_admin(request)

    total_citas        = Cita.objects.count()
    citas_confirmadas  = Cita.objects.filter(estado='confirmada').count()
    citas_canceladas   = Cita.objects.filter(estado='cancelada').count()
    citas_realizadas   = Cita.objects.filter(estado='realizada').count()

    # Citas por especialidad
    por_especialidad = (
        Especialidad.objects
        .annotate(total=Count('medicos__citas'))
        .values('nombre', 'total')
        .order_by('-total')
    )

    # Ocupación de médicos: cuántas citas tiene cada uno
    ocupacion_medicos = (
        Medico.objects
        .annotate(
            total_citas=Count('citas'),
            citas_realizadas=Count('citas', filter=Q(citas__estado='realizada')),
        )
        .values('nombre', 'total_citas', 'citas_realizadas')
        .order_by('-total_citas')
    )

    # Ocupación de salas
    ocupacion_salas = (
        Sala.objects
        .annotate(
            total_agendas=Count('agendas'),
            agendas_ocupadas=Count('agendas', filter=Q(agendas__estado='ocupado')),
        )
        .values('nombre', 'tipo', 'estado', 'total_agendas', 'agendas_ocupadas')
        .order_by('nombre')
    )

    context = {
        'total_citas':       total_citas,
        'citas_confirmadas': citas_confirmadas,
        'citas_canceladas':  citas_canceladas,
        'citas_realizadas':  citas_realizadas,
        'por_especialidad':  por_especialidad,
        'ocupacion_medicos': ocupacion_medicos,
        'ocupacion_salas':   ocupacion_salas,
    }
    return render(request, 'core/reporte_general.html', context)
