from django.shortcuts import render, redirect, get_object_or_404
from formtools.wizard.views import SessionWizardView
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import EscuelaForm, EntrenadorForm, AlumnoForm
from redepse.models import Escuela, Entrenador, Alumno

# ----------------------------
# Wizard para registrar Escuela
# ----------------------------
@method_decorator(login_required, name='dispatch')
class RegistroWizard(SessionWizardView):
    form_list = [("escuela", EscuelaForm)]
    template_name = "registro/escuela_form.html"

    def done(self, form_list, **kwargs):
        escuela_data = form_list[0].cleaned_data
        # Asociar la escuela al usuario logueado
        Escuela.objects.create(
            **escuela_data,
            solicitud_enviada=True,
            user=self.request.user
        )
        return redirect("escuelas:entrenadores")


# ---------------------------------------
# Formset para entrenadores (paso independiente)
# ---------------------------------------
@login_required
def entrenadores_view(request):
    # Trae la escuela del usuario logueado
    escuela = Escuela.objects.filter(solicitud_enviada=True, user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")  # si no existe, crear primero la escuela

    EntrenadorFormSet = modelformset_factory(
        Entrenador, form=EntrenadorForm, extra=1, can_delete=True
    )

    if request.method == "POST":
        formset = EntrenadorFormSet(request.POST, queryset=Entrenador.objects.none())
        if formset.is_valid():
            for f in formset.cleaned_data:
                if f:
                    f.pop("DELETE", None)  # <--- sacamos DELETE si existe
                    Entrenador.objects.create(escuela=escuela, **f)
            return redirect("escuelas:alumnos")
    else:
        formset = EntrenadorFormSet(queryset=Entrenador.objects.none())


    return render(request, "entrenadores_form.html", {"formset": formset})



# ---------------------------------------
# Formset para alumnos (paso independiente)
# ---------------------------------------
@login_required
def alumnos_view(request):
    escuela = Escuela.objects.filter(solicitud_enviada=True, user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")  # si no existe, crear primero la escuela

    AlumnoFormSet = modelformset_factory(
        Alumno, form=AlumnoForm, extra=1, can_delete=True
    )

    if request.method == "POST":
        formset = AlumnoFormSet(request.POST, queryset=Alumno.objects.none())
        if formset.is_valid():
            for f in formset.cleaned_data:
                if f:
                    f.pop("DELETE", None)  # <--- sacamos DELETE si existe
                    Alumno.objects.create(escuela=escuela, **f)
            return redirect("escuelas:estado")
    else:
        formset = AlumnoFormSet(queryset=Alumno.objects.none())

    return render(request, "alumnos_form.html", {"formset": formset})



# ---------------------------------------
# Estado de la solicitud
# ---------------------------------------
@login_required
def estado_solicitud(request):
    escuela = Escuela.objects.filter(user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")
    return render(request, "estado.html", {"escuela": escuela})