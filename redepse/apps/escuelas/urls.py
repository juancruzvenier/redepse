from django.urls import path
from . import views

app_name = "escuelas"

urlpatterns = [
    path("wizard/", views.RegistroWizard.as_view(), name="wizard"),
    path("entrenadores/", views.entrenadores_view, name="entrenadores"),
    path('entrenadores/entrenadores_api/', views.entrenadores_api, name='entrenadores_api'),
    path('entrenadores/entrenadores_api/delete/<int:id>/', views.eliminar_entrenador, name='eliminar_entrenador'),
    path("alumnos/", views.alumnos_view, name="alumnos"),
    path("estado/", views.estado_solicitud, name="estado"),
]