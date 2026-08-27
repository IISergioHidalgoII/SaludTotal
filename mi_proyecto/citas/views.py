from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from datetime import datetime, date, timedelta, time as dt_time
import calendar as cal_module
from collections import defaultdict

from usuarios.models import Especialidad, Medico, Paciente
from .models import Agenda, Cita, Notificacion, Sala
from .forms import AgendaForm
from .services import _enviar_email, _auto_confirmar_pendientes

MESES_ES = {
    1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril',
    5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto',
    9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre',
}

DIAS_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

# Bloques de 30 min, 08:00-18:00 (20 slots por día).
# Se pre-calculan una vez al arranque para no recomputar en cada request.
BLOQUES = []
for _h in range(8, 18):
    for _m in (0, 30):
        _ini = dt_time(_h, _m)
        _fin = dt_time(_h, _m + 30) if _m == 0 else (dt_time(_h + 1, 0) if _h < 17 else dt_time(18, 0))
        BLOQUES.append((_ini, _fin))


# ── Helper: enviar email y registrar Notificacion ────────────

def _enviar_email(destinatario_email, asunto, mensaje, cita, tipo_notif):
    """
    Registra la notificación en BD y envía el email.
    El registro persiste aunque el envío falle, con estado_envio='fallido'.
    tipo_notif: 'confirmacion' | 'cancelacion' | 'recordatorio' | 'cambio'
    """
    notif = Notificacion.objects.create(
        cita=cita,
        tipo=tipo_notif,
        mensaje=mensaje,
        estado_envio='pendiente',
    )
    if destinatario_email:
        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario_email],
                fail_silently=False,
            )
            notif.estado_envio = 'enviado'
            notif.fecha_envio  = datetime.now()
        except Exception:
            notif.estado_envio = 'fallido'
        notif.save()


# ── Helper: auto-confirmar citas pendientes sin respuesta ─────

def _auto_confirmar_pendientes(medico):
    """
    Confirma automáticamente citas pendientes sin respuesta del médico en > 2h.
    Se llama de forma lazy desde las vistas del médico (dashboard, panel citas)
    para no requerir una tarea programada (cron/Celery).
    """
    limite = datetime.now() - timedelta(hours=2)
    pendientes = Cita.objects.filter(
        medico=medico,
        estado='pendiente',
        creado_en__lte=limite,
    ).select_related('paciente__usuario', 'medico__especialidad', 'agenda')
    for cita in pendientes:
        cita.estado = 'confirmada'
        cita.save()
        asunto  = 'Clínica Salud Total — Cita confirmada automáticamente'
        sala_txt = f'\n  Sala: {cita.agenda.sala.nombre}' if cita.agenda.sala else ''
        mensaje = (
            f'Hola {cita.paciente.nombre},\n\n'
            f'Tu cita ha sido confirmada automáticamente (el médico no respondió en 2 horas):\n'
            f'  Médico: Dr(a). {cita.medico.nombre}\n'
            f'  Especialidad: {cita.medico.especialidad.nombre}\n'
            f'  Fecha: {cita.agenda.fecha}\n'
            f'  Hora: {cita.hora}{sala_txt}\n\n'
            f'Te esperamos en la clínica.\n\n'
            f'— Clínica Salud Total'
        )
        _enviar_email(cita.paciente.usuario.email, asunto, mensaje, cita, 'confirmacion')


# ── Paso 1: Elegir especialidad ────────────────────────────────

@login_required
def reservar_paso1(request):
    especialidades = Especialidad.objects.all()
    return render(request, 'citas/reservar_paso1.html', {
        'especialidades': especialidades,
    })


# ── Paso 2: Elegir médico ──────────────────────────────────────

@login_required
def reservar_paso2(request, especialidad_id):
    especialidad = get_object_or_404(Especialidad, pk=especialidad_id)
    medicos = Medico.objects.filter(especialidad=especialidad).select_related('usuario')
    return render(request, 'citas/reservar_paso2.html', {
        'especialidad': especialidad,
        'medicos': medicos,
    })


# ── Paso 3: Elegir horario disponible (vista calendario) ──────

@login_required
def reservar_paso3(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id)
    agendas = Agenda.objects.filter(
        medico=medico,
        estado='disponible',
    ).order_by('fecha', 'hora_inicio')

    # Agrupar slots por fecha
    slots_por_fecha = defaultdict(list)
    for agenda in agendas:
        slots_por_fecha[agenda.fecha].append(agenda)

    fechas_disponibles_str = {f.strftime('%Y-%m-%d') for f in slots_por_fecha}

    # Fecha seleccionada por GET param
    fecha_sel = None
    fecha_sel_str = request.GET.get('fecha', '')
    if fecha_sel_str:
        try:
            fecha_sel = datetime.strptime(fecha_sel_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    slots_dia = slots_por_fecha.get(fecha_sel, [])

    # Construir un calendario por cada mes que tenga slots
    meses = sorted({(f.year, f.month) for f in slots_por_fecha})
    if not meses:
        t = date.today()
        meses = [(t.year, t.month)]

    calendarios = []
    for year, month in meses:
        semanas_raw = cal_module.monthcalendar(year, month)
        semanas = []
        for semana in semanas_raw:
            dias = []
            for day in semana:
                if day == 0:
                    dias.append({'day': 0, 'fecha_str': None, 'disponible': False})
                else:
                    fs = date(year, month, day).strftime('%Y-%m-%d')
                    dias.append({
                        'day': day,
                        'fecha_str': fs,
                        'disponible': fs in fechas_disponibles_str,
                    })
            semanas.append(dias)
        calendarios.append({
            'year': year,
            'month': month,
            'nombre_mes': MESES_ES[month],
            'semanas': semanas,
        })

    return render(request, 'citas/reservar_paso3.html', {
        'medico':       medico,
        'calendarios':  calendarios,
        'fecha_sel':    fecha_sel,
        'fecha_sel_str': fecha_sel_str,
        'slots_dia':    slots_dia,
    })


# ── Paso 4: Confirmar y guardar cita ──────────────────────────

@login_required
def reservar_confirmar(request, agenda_id):
    # Buscar la agenda sin filtrar por estado — manejar el caso gracefully
    agenda = get_object_or_404(Agenda, pk=agenda_id)

    # Si la agenda ya fue ocupada (doble submit), redirigir sin error
    if agenda.estado == 'ocupado':
        messages.info(request, 'Este horario ya fue reservado.')
        return redirect('citas:mis_citas')

    if request.method == 'POST':
        # Re-verificar estado en el POST (condición de carrera)
        agenda.refresh_from_db()
        if agenda.estado != 'disponible':
            messages.warning(request, 'Este horario ya no está disponible.')
            return redirect('citas:reservar_paso1')

        # Verificar que el paciente tenga perfil
        try:
            paciente = request.user.perfil_paciente
        except Paciente.DoesNotExist:
            messages.error(request, 'Debes completar tu perfil de paciente antes de reservar.')
            return redirect('usuarios:perfil')

        # Crear la cita como PENDIENTE — el médico debe confirmar
        cita = Cita.objects.create(
            paciente=paciente,
            medico=agenda.medico,
            agenda=agenda,
            hora=agenda.hora_inicio,
            estado='pendiente',
            sala=agenda.sala,
        )
        agenda.estado = 'ocupado'
        agenda.save()

        # ── Email al paciente: solicitud recibida ────────────
        sala_txt = f'\n  Sala: {agenda.sala.nombre}' if agenda.sala else ''
        _enviar_email(
            paciente.usuario.email,
            'Clínica Salud Total — Solicitud de cita recibida',
            (
                f'Hola {paciente.nombre},\n\n'
                f'Tu solicitud de cita ha sido recibida y está pendiente de confirmación:\n'
                f'  Médico: Dr(a). {agenda.medico.nombre}\n'
                f'  Especialidad: {agenda.medico.especialidad.nombre}\n'
                f'  Fecha: {agenda.fecha}\n'
                f'  Hora: {agenda.hora_inicio}{sala_txt}\n\n'
                f'El médico tiene 2 horas para confirmar o rechazar.\n'
                f'Si no responde, la cita se confirmará automáticamente.\n\n'
                f'— Clínica Salud Total'
            ),
            cita, 'recordatorio',
        )

        # ── Email al médico: nueva solicitud ─────────────────
        _enviar_email(
            agenda.medico.usuario.email,
            'Clínica Salud Total — Nueva solicitud de cita',
            (
                f'Dr(a). {agenda.medico.nombre},\n\n'
                f'Has recibido una nueva solicitud de cita:\n'
                f'  Paciente: {paciente.nombre}\n'
                f'  Fecha: {agenda.fecha}\n'
                f'  Hora: {agenda.hora_inicio}{sala_txt}\n\n'
                f'Ingresa a la plataforma para confirmar o rechazar la cita.\n'
                f'Si no respondes en 2 horas, se confirmará automáticamente.\n\n'
                f'— Clínica Salud Total'
            ),
            cita, 'recordatorio',
        )

        messages.success(request, f'¡Solicitud enviada! El médico confirmará tu cita en las próximas 2 horas.')
        return redirect('citas:mis_citas')

    return render(request, 'citas/reservar_confirmar.html', {'agenda': agenda})


# ── Mis citas ─────────────────────────────────────────────────

@login_required
def mis_citas(request):
    try:
        paciente = request.user.perfil_paciente
        citas = Cita.objects.filter(paciente=paciente).select_related(
            'medico__especialidad', 'agenda__sala'
        ).order_by('-agenda__fecha')
    except Paciente.DoesNotExist:
        citas = []
    return render(request, 'citas/mis_citas.html', {'citas': citas})


# ── Cancelar cita ─────────────────────────────────────────────

@login_required
def cancelar_cita(request, cita_id):
    try:
        paciente = request.user.perfil_paciente
    except Paciente.DoesNotExist:
        return redirect('citas:mis_citas')

    cita = get_object_or_404(Cita, pk=cita_id, paciente=paciente)

    if request.method == 'POST':
        if cita.estado in ('pendiente', 'confirmada'):
            cita.estado = 'cancelada'
            cita.sala   = None
            cita.save()
            cita.agenda.estado = 'disponible'
            cita.agenda.save()

            # ── Email al paciente ────────────────────────────
            _enviar_email(
                paciente.usuario.email,
                'Clínica Salud Total — Cita cancelada',
                (
                    f'Hola {paciente.nombre},\n\n'
                    f'Tu cita ha sido cancelada:\n'
                    f'  Médico: Dr(a). {cita.medico.nombre}\n'
                    f'  Fecha: {cita.agenda.fecha}  Hora: {cita.hora}\n\n'
                    f'Puedes reservar una nueva cita cuando quieras.\n\n'
                    f'— Clínica Salud Total'
                ),
                cita, 'cancelacion',
            )

            # ── Email al médico avisando de la cancelación ───
            _enviar_email(
                cita.medico.usuario.email,
                'Clínica Salud Total — Cita cancelada por el paciente',
                (
                    f'Dr(a). {cita.medico.nombre},\n\n'
                    f'El paciente {paciente.nombre} canceló su cita:\n'
                    f'  Fecha: {cita.agenda.fecha}  Hora: {cita.hora}\n\n'
                    f'El horario ha quedado disponible nuevamente.\n\n'
                    f'— Clínica Salud Total'
                ),
                cita, 'cancelacion',
            )

            messages.success(request, 'Cita cancelada correctamente.')
        else:
            messages.warning(request, 'Esta cita no puede cancelarse.')
        return redirect('citas:mis_citas')

    return render(request, 'citas/cancelar_cita.html', {'cita': cita})


# ── Médico: confirmar cita ───────────────────────────────────

@login_required
def confirmar_cita_medico(request, cita_id):
    """El médico confirma manualmente una cita pendiente."""
    medico = _get_medico_o_403(request)
    cita   = get_object_or_404(Cita, pk=cita_id, medico=medico, estado='pendiente')
    if request.method == 'POST':
        cita.estado = 'confirmada'
        cita.save()
        sala_txt = f'\n  Sala: {cita.agenda.sala.nombre}' if cita.agenda.sala else ''
        _enviar_email(
            cita.paciente.usuario.email,
            'Clínica Salud Total — Cita confirmada',
            (
                f'Hola {cita.paciente.nombre},\n\n'
                f'El médico ha confirmado tu cita:\n'
                f'  Dr(a). {cita.medico.nombre}\n'
                f'  Especialidad: {cita.medico.especialidad.nombre}\n'
                f'  Fecha: {cita.agenda.fecha}\n'
                f'  Hora: {cita.hora}{sala_txt}\n\n'
                f'Te esperamos. Si necesitas cancelar, ingresa a la plataforma.\n\n'
                f'— Clínica Salud Total'
            ),
            cita, 'confirmacion',
        )
        messages.success(request, f'Cita de {cita.paciente.nombre} confirmada.')
    return redirect('consultas:citas_medico')


# ── Médico: rechazar cita ─────────────────────────────────────

@login_required
def rechazar_cita_medico(request, cita_id):
    """El médico rechaza una cita pendiente y libera la agenda."""
    medico = _get_medico_o_403(request)
    cita   = get_object_or_404(Cita, pk=cita_id, medico=medico, estado='pendiente')
    if request.method == 'POST':
        cita.estado = 'cancelada'
        cita.sala   = None
        cita.save()
        cita.agenda.estado = 'disponible'
        cita.agenda.save()
        _enviar_email(
            cita.paciente.usuario.email,
            'Clínica Salud Total — Cita no confirmada',
            (
                f'Hola {cita.paciente.nombre},\n\n'
                f'Lo sentimos, el médico no pudo confirmar tu cita:\n'
                f'  Dr(a). {cita.medico.nombre}\n'
                f'  Fecha: {cita.agenda.fecha}  Hora: {cita.hora}\n\n'
                f'Puedes reservar otro horario disponible desde la plataforma.\n\n'
                f'— Clínica Salud Total'
            ),
            cita, 'cancelacion',
        )
        messages.warning(request, f'Cita de {cita.paciente.nombre} rechazada. El horario quedó libre.')
    return redirect('consultas:citas_medico')


# ══════════════════════════════════════════════════════════════
#  VISTAS DEL MÉDICO — Gestión de agenda
# ══════════════════════════════════════════════════════════════

def _get_medico_o_403(request):
    """Devuelve el perfil Medico del usuario actual o lanza PermissionDenied."""
    try:
        return request.user.perfil_medico
    except Medico.DoesNotExist:
        raise PermissionDenied


def _sala_libre_para_dia(fecha, medico):
    """
    Determina qué sala de consulta asignar para un día dado:
    1. Si el médico ya tiene una sala asignada ese día, la reutiliza
       (un médico trabaja siempre en la misma sala durante el día).
    2. Si no, elige la primera sala de consulta disponible que no esté
       bloqueada por otro médico ese día.
    Las salas se bloquean a nivel de fecha completa, no por franja horaria,
    para reflejar que una sala es ocupada por un médico todo el día.
    """
    ya_id = (
        Agenda.objects
        .filter(medico=medico, fecha=fecha, sala__isnull=False)
        .values_list('sala_id', flat=True)
        .first()
    )
    if ya_id:
        try:
            return Sala.objects.get(pk=ya_id, estado='disponible')
        except Sala.DoesNotExist:
            pass
    bloqueadas = set(
        Agenda.objects
        .filter(fecha=fecha, sala__isnull=False)
        .exclude(medico=medico)
        .values_list('sala_id', flat=True)
        .distinct()
    )
    return (
        Sala.objects
        .filter(tipo='consulta', estado='disponible')
        .exclude(pk__in=bloqueadas)
        .order_by('nombre')
        .first()
    )


@login_required
def agenda_medico(request):
    """Lista todos los horarios del médico logueado."""
    medico = _get_medico_o_403(request)
    agendas = Agenda.objects.filter(medico=medico).select_related('sala').order_by('fecha', 'hora_inicio')
    return render(request, 'citas/agenda_medico.html', {'agendas': agendas})


@login_required
def agenda_crear(request):
    """Grilla semanal: el médico marca celdas (día × bloque horario) para crear slots."""
    medico = _get_medico_o_403(request)

    # Semana a mostrar (lunes de la semana)
    hoy = date.today()
    semana_str = request.GET.get('semana') or request.POST.get('semana', '')
    try:
        lunes = datetime.strptime(semana_str, '%Y-%m-%d').date()
        # Ajustar al lunes de esa semana
        lunes -= timedelta(days=lunes.weekday())
    except ValueError:
        lunes = hoy - timedelta(days=hoy.weekday())

    semana_anterior = (lunes - timedelta(weeks=1)).strftime('%Y-%m-%d')
    semana_siguiente = (lunes + timedelta(weeks=1)).strftime('%Y-%m-%d')
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]

    # Slots del médico esta semana
    existentes = {
        (a.fecha, a.hora_inicio): a
        for a in Agenda.objects.filter(
            medico=medico, fecha__in=dias_semana
        ).select_related('sala')
    }

    # Salas bloqueadas por día por OTROS médicos {fecha: set(sala_ids)}
    salas_bloqueadas_por_dia = defaultdict(set)
    for row in Agenda.objects.filter(
        fecha__in=dias_semana, sala__isnull=False
    ).exclude(medico=medico).values('fecha', 'sala_id').distinct():
        salas_bloqueadas_por_dia[row['fecha']].add(row['sala_id'])

    # Sala ya asignada a este médico por día {fecha: sala_id}
    sala_propia_por_dia = dict(
        Agenda.objects.filter(
            medico=medico, fecha__in=dias_semana, sala__isnull=False
        ).values_list('fecha', 'sala_id').distinct()
    )

    # IDs de salas de consulta disponibles
    consulta_ids = set(
        Sala.objects.filter(tipo='consulta', estado='disponible').values_list('pk', flat=True)
    )
    total_salas_consulta = len(consulta_ids)

    if request.method == 'POST':
        slots_recibidos = request.POST.getlist('slot')
        sala_id = request.POST.get('sala_id')
        sala_forzada = None
        if sala_id:
            try:
                sala_forzada = Sala.objects.get(pk=sala_id, estado='disponible')
            except Sala.DoesNotExist:
                pass

        creados = 0
        sin_sala = 0
        for slot in slots_recibidos:
            try:
                fecha_s, hi_s, hf_s = slot.split('|')
                slot_fecha = datetime.strptime(fecha_s, '%Y-%m-%d').date()
                slot_hi    = datetime.strptime(hi_s, '%H:%M').time()
                slot_hf    = datetime.strptime(hf_s, '%H:%M').time()
            except (ValueError, AttributeError):
                continue
            if slot_fecha < hoy:
                continue

            # Sala: bloqueada por día para otros médicos; mismo médico reutiliza la suya
            if sala_forzada:
                bloqueada = sala_forzada.pk in salas_bloqueadas_por_dia.get(slot_fecha, set())
                sala_slot  = _sala_libre_para_dia(slot_fecha, medico) if bloqueada else sala_forzada
            else:
                sala_slot = _sala_libre_para_dia(slot_fecha, medico)
            if sala_slot is None:
                sin_sala += 1

            try:
                _, created = Agenda.objects.get_or_create(
                    medico=medico,
                    fecha=slot_fecha,
                    hora_inicio=slot_hi,
                    defaults={'hora_fin': slot_hf, 'estado': 'disponible', 'sala': sala_slot},
                )
                if created:
                    creados += 1
            except IntegrityError:
                # Colisión en unique_sala_fecha_hora: otro médico ocupó la misma sala simultáneamente
                sin_sala += 1

        if creados:
            msg = f'{creados} horario(s) agregado(s) correctamente.'
            if sin_sala:
                msg += f' Atención: {sin_sala} horario(s) quedaron sin sala de consulta disponible.'
            messages.success(request, msg)
        else:
            messages.info(request, 'No se agregaron horarios nuevos (ya existían o no seleccionaste ninguno).')
        return redirect('citas:agenda_medico')

    # Construir grilla: filas=bloques, cols=días
    grilla = []
    for ini, fin in BLOQUES:
        fila = {
            'label': f'{ini.strftime("%H:%M")} – {fin.strftime("%H:%M")}',
            'celdas': [],
        }
        for dia in dias_semana:
            agenda_obj = existentes.get((dia, ini))
            estado = agenda_obj.estado if agenda_obj else None
            sala   = agenda_obj.sala   if agenda_obj else None
            valor  = f'{dia.strftime("%Y-%m-%d")}|{ini.strftime("%H:%M")}|{fin.strftime("%H:%M")}'
            # Cuántas salas de consulta quedan libres para este día
            tiene_sala_hoy = dia in sala_propia_por_dia
            if tiene_sala_hoy:
                salas_libres = 1  # Médico ya tiene sala para hoy, la reutilizará
            else:
                bloqueadas_hoy = salas_bloqueadas_por_dia.get(dia, set()) & consulta_ids
                salas_libres   = max(0, total_salas_consulta - len(bloqueadas_hoy))
            fila['celdas'].append({
                'dia':           dia,
                'valor':         valor,
                'estado':        estado,
                'sala':          sala,
                'pasado':        dia < hoy,
                'salas_libres':  salas_libres,
                'total_salas':   total_salas_consulta,
                'tiene_sala_hoy': tiene_sala_hoy,
            })
        grilla.append(fila)

    # Cabeceras con label + fecha + fecha_obj para comparar en template
    cabeceras = [
        {
            'label':     DIAS_ES[i],
            'fecha':     d.strftime('%d/%m'),
            'fecha_obj': d,
            'fin_semana': i >= 5,
        }
        for i, d in enumerate(dias_semana)
    ]

    return render(request, 'citas/agenda_grilla.html', {
        'grilla':           grilla,
        'cabeceras':        cabeceras,
        'lunes':            lunes,
        'hoy':              hoy,
        'semana_str':       lunes.strftime('%Y-%m-%d'),
        'semana_anterior':  semana_anterior,
        'semana_siguiente': semana_siguiente,
        'dias_semana':      dias_semana,
        'salas':            Sala.objects.filter(estado='disponible').order_by('nombre'),
        'total_salas_consulta': total_salas_consulta,
    })


@login_required
def agenda_eliminar(request, agenda_id):
    """Elimina un slot de agenda si aún no tiene cita asignada."""
    medico = _get_medico_o_403(request)
    agenda = get_object_or_404(Agenda, pk=agenda_id, medico=medico)

    if request.method == 'POST':
        if agenda.estado == 'ocupado':
            messages.error(request, 'No puedes eliminar un horario que ya tiene una cita asignada.')
        else:
            agenda.delete()
            messages.success(request, 'Horario eliminado.')
        return redirect('citas:agenda_medico')

    return render(request, 'citas/agenda_confirmar_eliminar.html', {'agenda': agenda})
