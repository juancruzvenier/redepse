from django import forms
from django.forms import modelformset_factory
from redepse.models import Escuela, Entrenador, Alumno, Disciplina

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

class EntrenadorForm(forms.ModelForm):
    class Meta:
        model = Entrenador
        fields = ['nombre', 'apellido', 'dni_ent']

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'dni_alumno', 'fecha_nac']
