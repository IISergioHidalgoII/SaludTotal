from django.db import models
from citas.models import Cita


# ──────────────────────────────────────────────────────────────
#  CONSULTA
# ──────────────────────────────────────────────────────────────

class Consulta(models.Model):
    """
    Registro médico de una cita realizada.
    Relación 1:1 con Cita (solo citas en estado 'realizada' deben tener consulta).
    """
    cita = models.OneToOneField(
        Cita,
        on_delete=models.PROTECT,
        related_name='consulta',
    )
    observaciones = models.TextField(blank=True)
    fecha_consulta = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f'Consulta #{self.pk} — {self.cita}'


# ──────────────────────────────────────────────────────────────
#  DIAGNOSTICO
# ──────────────────────────────────────────────────────────────

class Diagnostico(models.Model):
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='diagnosticos',
    )
    # Código CIE-10 (ej: J06.9)
    codigo_cie10 = models.CharField(max_length=10, blank=True)
    descripcion = models.TextField()

    class Meta:
        verbose_name = 'Diagnóstico'
        verbose_name_plural = 'Diagnósticos'

    def __str__(self):
        if self.codigo_cie10:
            return f'{self.codigo_cie10} — {self.descripcion[:60]}'
        return self.descripcion[:60]


# ──────────────────────────────────────────────────────────────
#  PRESCRIPCION
# ──────────────────────────────────────────────────────────────

class Prescripcion(models.Model):
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='prescripciones',
    )
    medicamento = models.CharField(max_length=200)
    dosis = models.CharField(max_length=100)
    indicaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Prescripción'
        verbose_name_plural = 'Prescripciones'

    def __str__(self):
        return f'{self.medicamento} — {self.dosis}'
