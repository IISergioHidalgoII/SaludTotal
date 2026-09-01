from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import validar_rut
from .models import Usuario


class ValidacionRutTests(TestCase):
    def test_normaliza_rut_valido(self):
        self.assertEqual(validar_rut('12.345.678-5'), '12.345.678-5')

    def test_rechaza_digito_verificador_incorrecto(self):
        with self.assertRaises(ValidationError):
            validar_rut('12.345.678-9')


class AutenticacionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='paciente_test', password='ClaveSegura123!', rol='paciente'
        )

    def test_dashboard_redirige_a_usuario_anonimo(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('usuarios:login')}?next={reverse('core:dashboard')}",
            fetch_redirect_response=False,
        )

    def test_logout_por_get_no_cierra_sesion(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('usuarios:logout'))
        self.assertRedirects(response, reverse('core:index'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_por_post_cierra_sesion(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('usuarios:logout'))
        self.assertRedirects(response, reverse('core:index'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RolesTests(TestCase):
    def test_superusuario_tiene_acceso_de_admin_y_medico(self):
        usuario = Usuario.objects.create_superuser(
            username='admin_test', password='ClaveSegura123!'
        )
        self.assertTrue(usuario.es_admin)
        self.assertTrue(usuario.es_medico)

