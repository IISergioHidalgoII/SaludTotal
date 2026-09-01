from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class ControlAccesoTests(TestCase):
    def test_usuario_comun_no_puede_abrir_admin(self):
        usuario = Usuario.objects.create_user(
            username='usuario_test', password='ClaveSegura123!'
        )
        self.client.force_login(usuario)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 403)

    def test_paciente_no_puede_abrir_reportes(self):
        usuario = Usuario.objects.create_user(
            username='paciente_test', password='ClaveSegura123!', rol='paciente'
        )
        self.client.force_login(usuario)
        response = self.client.get(reverse('core:reporte_general'))
        self.assertEqual(response.status_code, 403)

