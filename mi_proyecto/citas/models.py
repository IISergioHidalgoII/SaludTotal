from django.db import models
from django.db.models import UniqueConstraint
from usuarios.models import Paciente, Medico


# ──────────────────────────────────────────────────────────────
#  SALA
# ──────────────────────────────────────────────────────────────

class Sala(models.Model):
    TIPOS = [
        ('consulta',      'Consulta'),
        ('procedimiento', 'Procedimiento'),
        ('urgencia',      'Urgencia'),
    ]
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupada',    'Ocupada'),
        ('mantencion', 'En Mantención'),
    ]

    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200, blank=True)
    capacidad = models.PositiveSmallIntegerField(default=1)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='consulta')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')

    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
        ordering = ['nombre']

    def __str__(self):
        # Pylance marca get_tipo_display() como desconocido, pero Django la
        # genera automáticamente en runtime para todo campo con choices=.
        return f'{self.nombre} ({self.get_tipo_display()})'  # type: ignore[attr-defined]


# ──────────────────────────────────────────────────────────────
#  AGENDA
# ──────────────────────────────────────────────────────────────

class Agenda(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupado',    'Ocupado'),
    ]

    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE,
        related_name='agendas',
    )
    sala = models.ForeignKey(
        'Sala',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendas',
        verbose_name='Sala',
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agenda'
        verbose_name_plural = 'Agendas'
        ordering = ['fecha', 'hora_inicio']
        constraints = [
            # Evita duplicados de horario para el mismo médico
            models.UniqueConstraint(
                fields=['medico', 'fecha', 'hora_inicio'],
                name='unique_medico_fecha_hora',
            ),
            # Evita que dos médicos usen la misma sala al mismo tiempo
            UniqueConstraint(
                fields=['sala', 'fecha', 'hora_inicio'],
                name='unique_sala_fecha_hora',
            ),
        ]

    def __str__(self):
        return f'{self.medico} — {self.fecha} {self.hora_inicio}'


# ──────────────────────────────────────────────────────────────
#  CITA
# ──────────────────────────────────────────────────────────────

class Cita(models.Model):
    ESTADOS = [
        ('pendiente',  'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada',  'Cancelada'),
        ('realizada',  'Realizada'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='citas',
    )
    # Desnormalizado intencionalmente para consultas directas sin JOIN a Agenda
    medico = models.ForeignKey(
        Medico,
        on_delete=models.PROTECT,
        related_name='citas',
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas',
    )
    agenda = models.OneToOneField(
        Agenda,
        on_delete=models.PROTECT,
        related_name='cita',
    )
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-agenda__fecha', 'hora']

    def __str__(self):
        return f'Cita #{self.pk} — {self.paciente} con {self.medico}'


# ──────────────────────────────────────────────────────────────
#  NOTIFICACION
# ──────────────────────────────────────────────────────────────

class Notificacion(models.Model):
    TIPOS = [
        ('confirmacion', 'Confirmación'),
        ('cancelacion',  'Cancelación'),
        ('cambio',       'Cambio'),
        ('recordatorio', 'Recordatorio'),
    ]
    ESTADOS_ENVIO = [
        ('pendiente', 'Pendiente'),
        ('enviado',   'Enviado'),
        ('fallido',   'Fallido'),
    ]

    cita = models.ForeignKey(
        Cita,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    estado_envio = models.CharField(max_length=20, choices=ESTADOS_ENVIO, default='pendiente')
    fecha_envio = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_envio']

    def __str__(self):
        # Pylance no reconoce get_tipo_display() ni cita_id porque son
        # atributos dinámicos que Django crea en runtime:
        #   - get_<campo>_display() -> para campos con choices=
        #   - <campo>_id          -> acceso directo al PK de un ForeignKey
        return f'{self.get_tipo_display()} — Cita #{self.cita_id}'  # type: ignore[attr-defined]
