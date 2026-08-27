from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
import string

from .forms import RegistroForm, VerificacionForm, LoginForm
from .models import Paciente, Usuario


def _generar_codigo():
    """Genera un código numérico de 6 dígitos."""
    return ''.join(random.choices(string.digits, k=6))


def registro(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        # Guardar usuario como inactivo hasta verificar email
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Generar código y guardarlo en sesión con expiración (5 min)
        codigo = _generar_codigo()
        expira = timezone.now().timestamp() + 300  # 5 minutos
        request.session['verificacion'] = {
            'codigo':   codigo,
            'expira':   expira,
            'user_id':  user.pk,
            'nombre':   form.cleaned_data['nombre_completo'],
            'rut':      form.cleaned_data['rut'],
            'telefono': form.cleaned_data.get('telefono', ''),
        }

        # Enviar código por email
        send_mail(
            subject='Clínica Salud Total — Código de verificación',
            message=(
                f'Hola {user.username},\n\n'
                f'Tu código de verificación es: {codigo}\n\n'
                f'Este código expira en 5 minutos.\n\n'
                f'Si no solicitaste este registro, ignora este mensaje.\n\n'
                f'— Clínica Salud Total'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        messages.info(request, f'Te enviamos un código de verificación a {user.email}. Ingrésalo abajo.')
        return redirect('usuarios:verificar')

    return render(request, 'usuarios/registro.html', {'form': form})


def verificar_email(request):
    """El paciente ingresa el código de 6 dígitos recibido por email."""
    datos = request.session.get('verificacion')
    if not datos:
        messages.error(request, 'No hay verificación pendiente. Regístrate primero.')
        return redirect('usuarios:registro')

    # Verificar si el código expiró
    if timezone.now().timestamp() > datos['expira']:
        # Eliminar usuario creado y limpiar sesión
        Usuario.objects.filter(pk=datos['user_id']).delete()
        del request.session['verificacion']
        messages.error(request, 'El código expiró (5 minutos). Por favor regístrate de nuevo.')
        return redirect('usuarios:registro')

    form = VerificacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Rate limiting: máx 5 intentos fallidos
        intentos = datos.get('intentos_fallidos', 0)
        if intentos >= 5:
            Usuario.objects.filter(pk=datos['user_id']).delete()
            del request.session['verificacion']
            messages.error(request, 'Demasiados intentos fallidos. Por favor regístrate de nuevo.')
            return redirect('usuarios:registro')

        ingresado = form.cleaned_data['codigo'].strip()
        if ingresado == datos['codigo']:
            # Activar usuario y crear perfil Paciente
            user = Usuario.objects.get(pk=datos['user_id'])
            user.is_active = True
            user.save()

            Paciente.objects.create(
                usuario=user,
                nombre=datos['nombre'],
                rut=datos['rut'],
                telefono=datos.get('telefono', ''),
            )

            del request.session['verificacion']
            login(request, user)
            messages.success(request, f'¡Cuenta verificada! Bienvenido, {user.username}.')
            return redirect('core:dashboard')
        else:
            datos['intentos_fallidos'] = datos.get('intentos_fallidos', 0) + 1
            request.session['verificacion'] = datos
            restantes = 5 - datos['intentos_fallidos']
            messages.error(request, f'Código incorrecto. Te quedan {restantes} intento(s).')

    # Calcular segundos restantes para mostrar en UI
    segundos_restantes = max(0, int(datos['expira'] - timezone.now().timestamp()))
    return render(request, 'usuarios/verificar.html', {
        'form':               form,
        'segundos_restantes': segundos_restantes,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'¡Hola, {user.username}!')
        next_url = request.GET.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('core:dashboard')
    return render(request, 'usuarios/login.html', {'form': form})


def user_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('core:index')


@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html', {'usuario': request.user})
