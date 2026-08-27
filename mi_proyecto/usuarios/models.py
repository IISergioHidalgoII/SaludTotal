from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado.
    Roles del sistema: 'admin', 'medico', 'paciente'.
    """
    ROLES = [
        ('admin',    'Administrador'),
        ('medico',   'Médico'),
        ('paciente', 'Paciente'),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='paciente',
        verbose_name='Rol',
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Biografía',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username

    # ── Propiedades de conveniencia ────────────────────────────
    @property
    def es_admin(self):
        return self.rol == 'admin' or self.is_superuser

    @property
    def es_medico(self):
        return self.rol == 'medico' or self.is_superuser

    @property
    def es_paciente(self):
        return self.rol == 'paciente'


# ──────────────────────────────────────────────────────────────
#  ESPECIALIDADES
# ──────────────────────────────────────────────────────────────

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ──────────────────────────────────────────────────────────────
#  PERFILES DE USUARIO
# ──────────────────────────────────────────────────────────────

class Paciente(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_paciente',
    )
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    antecedentes_medicos = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

    def __str__(self):
        return f'{self.nombre} ({self.rut})'


class Medico(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_medico',
    )
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        related_name='medicos',
    )
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Médico'
        verbose_name_plural = 'Médicos'

    def __str__(self):
        return f'Dr(a). {self.nombre} — {self.especialidad}'


class Administrador(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_administrador',
    )
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return f'{self.nombre} ({self.cargo})'
