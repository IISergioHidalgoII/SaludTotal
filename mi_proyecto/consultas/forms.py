from django import forms
from .models import Consulta, Diagnostico, Prescripcion


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ['fecha_consulta', 'observaciones']
        widgets = {
            'fecha_consulta': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones':  forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['codigo_cie10', 'descripcion']
        widgets = {
            'codigo_cie10': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: J06.9',
            }),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PrescripcionForm(forms.ModelForm):
    class Meta:
        model = Prescripcion
        fields = ['medicamento', 'dosis', 'indicaciones']
        widgets = {
            'medicamento':  forms.TextInput(attrs={'class': 'form-control'}),
            'dosis':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 500mg cada 8 horas'}),
            'indicaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
