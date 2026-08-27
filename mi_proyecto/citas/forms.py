from django import forms
from datetime import date
from .models import Agenda


class AgendaForm(forms.ModelForm):
    class Meta:
        model = Agenda
        fields = ['fecha', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha':       forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin':    forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < date.today():
            raise forms.ValidationError('No puedes agregar horarios en fechas pasadas.')
        return fecha

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('hora_inicio')
        fin = cleaned.get('hora_fin')
        if inicio and fin and fin <= inicio:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        return cleaned
