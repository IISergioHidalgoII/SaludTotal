from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario


# ── Validador de RUT chileno ──────────────────────────────────

def _calcular_dv(rut_numerico):
    """
    Módulo 11 inverso: suma los dígitos del cuerpo multiplicados por el
    factor cíclico [2,3,4,5,6,7], de derecha a izquierda, y calcula el
    residuo. Si el resultado es 11 → '0'; si es 10 → 'K'; resto → str(n).
    """
    suma, factor = 0, 2
    for d in reversed(str(rut_numerico)):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def validar_rut(valor):
    """
    Acepta formatos: 12345678-9 / 12.345.678-9 / 123456789
    Retorna el RUT normalizado (con puntos y guión) o lanza ValidationError.
    """
    # Normalizar: quitar puntos y espacios, pasar a mayúsculas
    limpio = valor.replace('.', '').replace(' ', '').upper()
    if '-' not in limpio:
        # Asumir que el último carácter es el DV
        limpio = limpio[:-1] + '-' + limpio[-1]

    partes = limpio.split('-')
    if len(partes) != 2:
        raise forms.ValidationError('Formato de RUT inválido. Use 12.345.678-9')

    cuerpo, dv = partes
    if not cuerpo.isdigit():
        raise forms.ValidationError('El RUT solo debe contener números y el dígito verificador.')

    rut_num = int(cuerpo)
    if rut_num < 1_000_000 or rut_num > 99_999_999:
        raise forms.ValidationError('El RUT ingresado está fuera del rango válido.')

    dv_esperado = _calcular_dv(rut_num)
    if dv != dv_esperado:
        raise forms.ValidationError(
            f'El dígito verificador es incorrecto. Verifica tu RUT.'
        )

    # Devolver formateado con puntos
    cuerpo_fmt = f'{rut_num:,}'.replace(',', '.')
    return f'{cuerpo_fmt}-{dv}'


# ─────────────────────────────────────────────────────────────

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    nombre_completo = forms.CharField(
        max_length=200,
        label='Nombre completo',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    rut = forms.CharField(
        max_length=12,
        label='RUT',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 xxxx xxxx'}),
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'nombre_completo', 'rut', 'telefono', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_rut(self):
        from usuarios.models import Paciente
        rut_normalizado = validar_rut(self.cleaned_data['rut'])
        if Paciente.objects.filter(rut=rut_normalizado).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con ese RUT.')
        return rut_normalizado


class VerificacionForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        label='Código de verificación',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
        }),
    )


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
