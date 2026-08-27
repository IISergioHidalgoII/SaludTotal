from django.db import models


class ModeloBase(models.Model):
    """
    Modelo abstracto base con campos de auditoría.
    """
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
