from django import forms
from django.forms import modelformset_factory
from apps.escuelas.models import Escuela, Entrenador, Alumno, Disciplina, Periodo, Tutor
from datetime import date

# Lista de localidades de Santiago del Estero
LOCALIDADES_SDE = [
    ('', 'Seleccione una localidad'),
    ('Santiago del Estero', 'Santiago del Estero (Capital)'),
    ('La Banda', 'La Banda'),
    ('Frías', 'Frías'),
    ('Añatuya', 'Añatuya'),
    ('Quimilí', 'Quimilí'),
    ('Loreto', 'Loreto'),
    ('Clodomira', 'Clodomira'),
    ('Termas de Río Hondo', 'Termas de Río Hondo'),
    ('Monte Quemado', 'Monte Quemado'),
    ('Sumampa', 'Sumampa'),
    ('Fernández', 'Fernández'),
    ('Selva', 'Selva'),
    ('Icaño', 'Icaño'),
    ('Pinto', 'Pinto'),
    ('Villa Atamisqui', 'Villa Atamisqui'),
    ('Bandera', 'Bandera'),
    ('Los Telares', 'Los Telares'),
    ('Villa Ojo de Agua', 'Villa Ojo de Agua'),
    ('Suncho Corral', 'Suncho Corral'),
]

class EscuelaForm(forms.ModelForm):
    localidad = forms.ChoiceField(
        choices=LOCALIDADES_SDE,
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'})
    )
    
    class Meta:
        model = Escuela
        fields = ['nombre_esc', 'localidad', 'direccion', 'email', 'telefono1']
        widgets = {
            'nombre_esc': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: Escuela Deportiva Central'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: Av. Central 123'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'ejemplo@escuela.com'
            }),
            'telefono1': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: 3854123456',
                'pattern': '[0-9]+',
                'title': 'Solo se permiten números'
            }),
        }
    
    def clean_telefono1(self):
        telefono = self.cleaned_data['telefono1']
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono debe contener solo números.")
        return telefono

class DocumentacionForm(forms.Form):
    documento = forms.FileField(
        label="Nota al secretario Dapello",
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.doc,.docx,.pdf'
        }),
        help_text="Formatos aceptados: .doc, .docx, .pdf"
    )
    
    def clean_documento(self):
        documento = self.cleaned_data['documento']
        if documento:
            ext = documento.name.split('.')[-1].lower()
            if ext not in ['doc', 'docx', 'pdf']:
                raise forms.ValidationError("Solo se permiten archivos .doc, .docx o .pdf")
        return documento

class DisciplinaForm(forms.Form):
    disciplinas = forms.ModelMultipleChoiceField(
        queryset=Disciplina.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'disciplina-checkbox'}),
        required=True,
        label="Seleccione las disciplinas que impartirá"
    )

class EntrenadorForm(forms.ModelForm):
    class Meta:
        model = Entrenador
        fields = ['dni_ent', 'nombre', 'apellido', 'fecha_nac', 'email', 'telefono', 'domicilio']
        widgets = {
            'dni_ent': forms.NumberInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: 40123456'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: Juan'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: Pérez'
            }),
            'fecha_nac': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': date.today().isoformat()
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@email.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3854123456',
                'pattern': '[0-9]+'
            }),
            'domicilio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Calle Principal 123'
            }),
        }
    
    def clean_dni_ent(self):
        dni = self.cleaned_data['dni_ent']
        if dni <= 0:
            raise forms.ValidationError("El DNI debe ser un número positivo.")
        return dni
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El teléfono debe contener solo números.")
        return telefono

class TutorForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['dni_tutor', 'nombre', 'apellido', 'email', 'telefono1', 'domicilio']
        widgets = {
            'dni_tutor': forms.NumberInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: 40123456'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: María'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: González'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@email.com'
            }),
            'telefono1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3854123456',
                'pattern': '[0-9]+'
            }),
            'domicilio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Calle Principal 123'
            }),
        }

class AlumnoForm(forms.ModelForm):
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.none(),  # Se llenará dinámicamente
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
        required=True,
        label="Disciplina"
    )
    
    tutor = forms.ModelChoiceField(
        queryset=Tutor.objects.none(),  # Se llenará dinámicamente
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
        required=True,
        label="Tutor a cargo"
    )
    
    class Meta:
        model = Alumno
        fields = ['dni_alumno', 'nombre', 'apellido', 'fecha_nac', 'domicilio']
        widgets = {
            'dni_alumno': forms.NumberInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: 45987654'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: Carlos'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'placeholder': 'Ej: López'
            }),
            'fecha_nac': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': date.today().isoformat()
            }),
            'domicilio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Calle Principal 123'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        disciplinas_seleccionadas = kwargs.pop('disciplinas_seleccionadas', None)
        tutores_registrados = kwargs.pop('tutores_registrados', None)
        super().__init__(*args, **kwargs)
        
        if disciplinas_seleccionadas:
            self.fields['disciplina'].queryset = disciplinas_seleccionadas
        
        if tutores_registrados:
            self.fields['tutor'].queryset = tutores_registrados.order_by('apellido', 'nombre')