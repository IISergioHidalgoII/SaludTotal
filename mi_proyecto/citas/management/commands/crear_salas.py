from django.core.management.base import BaseCommand
from citas.models import Sala

SALAS_INICIALES = [
    # 2 salas de consulta por especialidad conceptual
    {'nombre': 'Sala C-01', 'tipo': 'consulta',      'ubicacion': 'Piso 1 — Ala Norte',  'capacidad': 1},
    {'nombre': 'Sala C-02', 'tipo': 'consulta',      'ubicacion': 'Piso 1 — Ala Norte',  'capacidad': 1},
    {'nombre': 'Sala C-03', 'tipo': 'consulta',      'ubicacion': 'Piso 1 — Ala Sur',    'capacidad': 1},
    {'nombre': 'Sala C-04', 'tipo': 'consulta',      'ubicacion': 'Piso 1 — Ala Sur',    'capacidad': 1},
    {'nombre': 'Sala C-05', 'tipo': 'consulta',      'ubicacion': 'Piso 2 — Cardiología','capacidad': 1},
    {'nombre': 'Sala C-06', 'tipo': 'consulta',      'ubicacion': 'Piso 2 — Cardiología','capacidad': 1},
    # 2 salas de procedimientos
    {'nombre': 'Sala P-01', 'tipo': 'procedimiento', 'ubicacion': 'Piso 2 — Ala Este',   'capacidad': 2},
    {'nombre': 'Sala P-02', 'tipo': 'procedimiento', 'ubicacion': 'Piso 2 — Ala Este',   'capacidad': 2},
    # 2 salas de urgencias
    {'nombre': 'Sala U-01', 'tipo': 'urgencia',      'ubicacion': 'Piso 1 — Urgencias',  'capacidad': 1},
    {'nombre': 'Sala U-02', 'tipo': 'urgencia',      'ubicacion': 'Piso 1 — Urgencias',  'capacidad': 1},
]


class Command(BaseCommand):
    help = 'Crea las salas iniciales de la Clínica Salud Total (idempotente).'

    def handle(self, *args, **options):
        creadas = 0
        for datos in SALAS_INICIALES:
            _, created = Sala.objects.get_or_create(
                nombre=datos['nombre'],
                defaults=datos,
            )
            if created:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ {datos["nombre"]} creada'))
            else:
                self.stdout.write(f'  — {datos["nombre"]} ya existe, omitida')

        self.stdout.write(self.style.SUCCESS(
            f'\nListo: {creadas} sala(s) nueva(s) creada(s). '
            f'Total en BD: {Sala.objects.count()}'
        ))
