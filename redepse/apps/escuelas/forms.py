from django import forms
from django.forms import modelformset_factory
from apps.escuelas.models import Escuela, Entrenador, Alumno, Disciplina, Periodo
from datetime import date

class EscuelaForm(forms.ModelForm):
    class Meta:
        model = Escuela
        fields = ['nombre_esc', 'direccion', 'localidad', 'telefono1', 'telefono2', 'email']


EntrenadorFormSet = modelformset_factory(
    Entrenador,
    fields=('nombre', 'apellido', 'dni_ent'),
    extra=1,  # mínimo 1 campo vacío
    can_delete=True
)

AlumnoFormSet = modelformset_factory(
    Alumno,
    fields=('nombre', 'apellido', 'dni_alumno', 'fecha_nac'),
    extra=1,
    can_delete=True
)

class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['disciplina']

'''
class EntrenadorForm(forms.ModelForm):
    class Meta:
        model = Entrenador
        fields = [
            "dni_ent", "nombre", "apellido", "fecha_nac",
            "email", "telefono", "domicilio", "periodo"
        ]
        widgets = {
            "fecha_nac": forms.DateInput(attrs={"type": "date", "max": date.today()}),
        }

    def clean_fecha_nac(self):
        fecha = self.cleaned_data["fecha_nac"]
        hoy = date.today()
        if (hoy.year - fecha.year) < 18:
            raise forms.ValidationError("El entrenador debe tener al menos 18 años.")
        return fecha
'''

class EntrenadorForm(forms.ModelForm):
    class Meta:
        model = Entrenador
        fields = [
            "dni_ent", "nombre", "apellido", "fecha_nac",
            "email", "telefono", "domicilio", "periodo"
        ]
        widgets = {
            "fecha_nac": forms.DateInput(attrs={"type": "date", "max": date.today()}),
            "periodo": forms.Select(attrs={"class": "form-control"})  # Añadir widget
        }

    def clean_dni_ent(self):
        dni = self.cleaned_data["dni_ent"]
        if Entrenador.objects.filter(dni_ent=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado.")
        return dni

    def clean_fecha_nac(self):
        fecha = self.cleaned_data["fecha_nac"]
        hoy = date.today()
        if (hoy.year - fecha.year) < 18:
            raise forms.ValidationError("El entrenador debe tener al menos 18 años.")
        return fecha


class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = [
            "dni_alumno", "nombre", "apellido", "fecha_nac",
            "domicilio", "dni_tutor"
        ]
        widgets = {
            "fecha_nac": forms.DateInput(attrs={"type": "date", "max": date.today()}),
       #     "periodo": forms.Select(attrs={"class": "form-control"})  # Añadir widget
        }

    def clean_dni_alumno(self):
        dni = self.cleaned_data["dni_alumno"]
        if Alumno.objects.filter(dni_alumno=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado.")
        return dni


'''
class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'dni_alumno', 'fecha_nac']
'''
