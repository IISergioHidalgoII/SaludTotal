"""
citas/services.py — Lógica de negocio reutilizable de la app citas.

Separada de views.py para que otros módulos (core, consultas) puedan
importarla sin generar importaciones circulares entre apps.
"""
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta

from .models import Cita, Notificacion


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
        asunto   = 'Clínica Salud Total — Cita confirmada automáticamente'
        sala_txt = f'\n  Sala: {cita.agenda.sala.nombre}' if cita.agenda.sala else ''
        mensaje  = (
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
