from django.contrib import admin
from redepse.models import Alumno, Entrenador, Disciplina  # todos tus modelos

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('dni_alumno', 'nombre')

@admin.register(Entrenador)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('dni_ent', 'nombre', 'email')

@admin.register(Disciplina)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('id_disciplina', 'disciplina')
