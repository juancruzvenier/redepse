from django.urls import path
from . import views

app_name = "escuelas"

urlpatterns = [
    path("registro/<str:paso>/", views.RegistroWizardView.as_view(), name="registro_wizard"),
    path("guardar-paso/<str:paso>/", views.guardar_paso, name="guardar_paso"),
    path("finalizar-registro/", views.finalizar_registro, name="finalizar_registro"),
    path("estado/", views.estado_solicitud, name="estado"),
]