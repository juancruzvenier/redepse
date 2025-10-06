from django.contrib import admin
from .models import *  # todos los modelos que quiera mostrar

@admin.register(Escuela)
class EscuelasAdmin(admin.ModelAdmin):
    list_display = ['nombre_esc', 'localidad']

@admin.register(Solicitudes)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['id_esc', 'estado']

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('dni_alumno', 'nombre', 'id_periodo')