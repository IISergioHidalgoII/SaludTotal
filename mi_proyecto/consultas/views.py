from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from citas.models import Cita
from citas.services import _auto_confirmar_pendientes
from usuarios.models import Medico, Paciente
from .models import Consulta, Diagnostico, Prescripcion
from .forms import ConsultaForm, DiagnosticoForm, PrescripcionForm


def _get_medico_o_403(request):
    try:
        return request.user.perfil_medico
    except Medico.DoesNotExist:
        raise PermissionDenied


# ── Citas del médico (pendientes/confirmadas) ─────────────────

@login_required
def citas_medico(request):
    medico = _get_medico_o_403(request)
    # Auto-confirmar pendientes sin respuesta > 2h
    _auto_confirmar_pendientes(medico)
    citas_pendientes  = Cita.objects.filter(medico=medico, estado='pendiente').select_related('paciente', 'agenda__sala').order_by('agenda__fecha', 'hora')
    citas_confirmadas = Cita.objects.filter(medico=medico, estado='confirmada').select_related('paciente', 'agenda__sala').order_by('agenda__fecha', 'hora')
    return render(request, 'consultas/citas_medico.html', {
        'citas_pendientes':  citas_pendientes,
        'citas_confirmadas': citas_confirmadas,
    })


# ── Registrar consulta ────────────────────────────────────────

@login_required
def registrar_consulta(request, cita_id):
    medico = _get_medico_o_403(request)
    cita = get_object_or_404(Cita, pk=cita_id, medico=medico, estado='confirmada')

    # Si ya tiene consulta, ir al detalle
    if hasattr(cita, 'consulta'):
        return redirect('consultas:detalle', consulta_id=cita.consulta.pk)

    form = ConsultaForm(request.POST or None)
    if form.is_valid():
        consulta = form.save(commit=False)
        consulta.cita = cita
        consulta.save()
        # Marcar la cita como realizada
        cita.estado = 'realizada'
        cita.save()
        messages.success(request, 'Consulta registrada correctamente.')
        return redirect('consultas:detalle', consulta_id=consulta.pk)

    return render(request, 'consultas/consulta_form.html', {
        'form': form,
        'cita': cita,
    })


# ── Detalle de consulta ───────────────────────────────────────

@login_required
def detalle_consulta(request, consulta_id):
    medico = _get_medico_o_403(request)
    consulta = get_object_or_404(Consulta, pk=consulta_id, cita__medico=medico)
    diagnosticos = consulta.diagnosticos.all()
    prescripciones = consulta.prescripciones.all()
    return render(request, 'consultas/detalle.html', {
        'consulta':      consulta,
        'diagnosticos':  diagnosticos,
        'prescripciones': prescripciones,
        'form_diag':     DiagnosticoForm(),
        'form_presc':    PrescripcionForm(),
    })


# ── Agregar diagnóstico ───────────────────────────────────────

@login_required
def agregar_diagnostico(request, consulta_id):
    medico = _get_medico_o_403(request)
    consulta = get_object_or_404(Consulta, pk=consulta_id, cita__medico=medico)

    if request.method == 'POST':
        form = DiagnosticoForm(request.POST)
        if form.is_valid():
            diag = form.save(commit=False)
            diag.consulta = consulta
            diag.save()
            messages.success(request, 'Diagnóstico agregado.')
    return redirect('consultas:detalle', consulta_id=consulta.pk)


# ── Agregar prescripción ──────────────────────────────────────

@login_required
def agregar_prescripcion(request, consulta_id):
    medico = _get_medico_o_403(request)
    consulta = get_object_or_404(Consulta, pk=consulta_id, cita__medico=medico)

    if request.method == 'POST':
        form = PrescripcionForm(request.POST)
        if form.is_valid():
            presc = form.save(commit=False)
            presc.consulta = consulta
            presc.save()
            messages.success(request, 'Prescripción agregada.')
    return redirect('consultas:detalle', consulta_id=consulta.pk)


# ── Eliminar diagnóstico ──────────────────────────────────────

@login_required
def eliminar_diagnostico(request, diag_id):
    medico = _get_medico_o_403(request)
    diag = get_object_or_404(Diagnostico, pk=diag_id, consulta__cita__medico=medico)
    consulta_id = diag.consulta_id
    if request.method == 'POST':
        diag.delete()
        messages.success(request, 'Diagnóstico eliminado.')
    return redirect('consultas:detalle', consulta_id=consulta_id)


# ── Eliminar prescripción ─────────────────────────────────────

@login_required
def eliminar_prescripcion(request, presc_id):
    medico = _get_medico_o_403(request)
    presc = get_object_or_404(Prescripcion, pk=presc_id, consulta__cita__medico=medico)
    consulta_id = presc.consulta_id
    if request.method == 'POST':
        presc.delete()
        messages.success(request, 'Prescripción eliminada.')
    return redirect('consultas:detalle', consulta_id=consulta_id)


# ── Editar observaciones de la consulta ──────────────────────

@login_required
def editar_consulta(request, consulta_id):
    medico   = _get_medico_o_403(request)
    consulta = get_object_or_404(Consulta, pk=consulta_id, cita__medico=medico)
    form = ConsultaForm(request.POST or None, instance=consulta)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Consulta actualizada.')
        return redirect('consultas:detalle', consulta_id=consulta.pk)
    return render(request, 'consultas/consulta_form.html', {
        'form':    form,
        'cita':    consulta.cita,
        'editar':  True,
        'consulta': consulta,
    })


# ══════════════════════════════════════════════════════════════
#  BÚSQUEDA DE PACIENTE POR RUT — Solo médicos
# ══════════════════════════════════════════════════════════════

@login_required
def buscar_paciente(request):
    """Médico busca un paciente por RUT o nombre para ver su historial."""
    _get_medico_o_403(request)
    resultados = []
    rut_query  = request.GET.get('rut', '').strip()

    if rut_query:
        from usuarios.forms import validar_rut
        # Intentar normalizar a formato almacenado (12.345.678-9)
        try:
            rut_normalizado = validar_rut(rut_query)
            qs = Paciente.objects.filter(rut=rut_normalizado)
        except Exception:
            # Si no es un RUT válido, buscar por nombre
            qs = Paciente.objects.filter(nombre__icontains=rut_query)

        if qs.count() == 1:
            return redirect('consultas:historial_paciente', paciente_id=qs.first().pk)
        elif qs.count() > 1:
            resultados = qs
        else:
            messages.warning(request, f'No se encontró ningún paciente con ese RUT o nombre.')

    return render(request, 'consultas/buscar_paciente.html', {
        'rut_query':  rut_query,
        'resultados': resultados,
    })


@login_required
def historial_paciente(request, paciente_id):
    """Médico ve todas las consultas de un paciente específico."""
    _get_medico_o_403(request)
    paciente   = get_object_or_404(Paciente, pk=paciente_id)
    consultas  = (
        Consulta.objects
        .filter(cita__paciente=paciente)
        .select_related('cita__medico__especialidad')
        .order_by('-fecha_consulta')
    )
    return render(request, 'consultas/historial_paciente.html', {
        'paciente':  paciente,
        'consultas': consultas,
    })


# ── Imprimir / exportar consulta como PDF ────────────────────

@login_required
def imprimir_consulta(request, consulta_id):
    """Vista de impresión — accesible por médico y por el paciente dueño."""
    # Médico: solo si tiene perfil de médico
    try:
        medico   = request.user.perfil_medico
        consulta = get_object_or_404(Consulta, pk=consulta_id, cita__medico=medico)
    except Medico.DoesNotExist:
        # Paciente: solo si tiene perfil de paciente y la consulta le pertenece
        try:
            paciente = request.user.perfil_paciente
            consulta = get_object_or_404(Consulta, pk=consulta_id, cita__paciente=paciente)
        except Paciente.DoesNotExist:
            raise PermissionDenied

    return render(request, 'consultas/imprimir.html', {
        'consulta':       consulta,
        'diagnosticos':   consulta.diagnosticos.all(),
        'prescripciones': consulta.prescripciones.all(),
    })


# ══════════════════════════════════════════════════════════════
#  VISTAS DEL PACIENTE — Ver historial médico
# ══════════════════════════════════════════════════════════════

@login_required
def detalle_consulta_paciente(request, consulta_id):
    """Detalle de una consulta — vista de solo lectura para el paciente."""
    from usuarios.models import Paciente
    try:
        paciente = request.user.perfil_paciente
    except Paciente.DoesNotExist:
        raise PermissionDenied

    consulta = get_object_or_404(Consulta, pk=consulta_id, cita__paciente=paciente)
    return render(request, 'consultas/detalle_paciente.html', {
        'consulta':       consulta,
        'diagnosticos':   consulta.diagnosticos.all(),
        'prescripciones': consulta.prescripciones.all(),
    })
