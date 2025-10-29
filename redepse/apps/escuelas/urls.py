from django.urls import path
from .forms import EscuelaForm, EntrenadorFormSet, AlumnoFormSet
from .views import RegistroWizard, entrenadores_view, alumnos_view, estado_solicitud

app_name = "escuelas"

urlpatterns = [
    path("wizard/", RegistroWizard.as_view(), name="wizard"),
    path("entrenadores/", entrenadores_view, name="entrenadores"),
    path("alumnos/", alumnos_view, name="alumnos"),
    path("estado/", estado_solicitud, name="estado"),
]
