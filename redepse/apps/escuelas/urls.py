from django.urls import path
from . import views

app_name = "escuelas"

urlpatterns = [
    path("wizard/", views.RegistroWizard.as_view(), name="wizard"),
    path("entrenadores/", views.entrenadores_view, name="entrenadores"),
    path('entrenadores/entrenadores_api/', views.entrenadores_api, name='entrenadores_api'),
    path('entrenadores/entrenadores_api/delete/<int:id>/', views.eliminar_entrenador, name='eliminar_entrenador'),
    path("alumnos/", views.alumnos_view, name="alumnos"),
    path('alumnos/alumnos_api/', views.alumnos_api, name='alumnos_api'),
    path('alumnos/alumnos_api/delete/<int:id>/', views.eliminar_alumno, name='eliminar_alumno'),
    path("estado/", views.estado_solicitud, name="estado"),
]