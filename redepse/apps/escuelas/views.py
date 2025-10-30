from django.shortcuts import render, redirect, get_object_or_404
from formtools.wizard.views import SessionWizardView
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import EscuelaForm, EntrenadorForm, AlumnoForm
from .models import Escuela, Entrenador, Alumno, Periodo
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


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

def entrenadores_view(request):
    form = EntrenadorForm()
    periodos = Periodo.objects.all().order_by("periodo")
    return render(request, "registro/entrenadores_form.html", {"form": form, "periodos": periodos})


@csrf_exempt
def entrenadores_api(request):
    if request.method == "GET":
        # Obtener solo los entrenadores de la escuela del usuario actual
        escuela = Escuela.objects.filter(user=request.user).first()
        if escuela:
            # Aquí necesitarías una relación entre Entrenador y Escuela
            # Por ahora traemos todos, pero deberías filtrar
            entrenadores = list(Entrenador.objects.values(
                'dni_ent', 'nombre', 'apellido', 'fecha_nac', 
                'email', 'telefono', 'domicilio', 'periodo'
            ))
        else:
            entrenadores = []
        return JsonResponse(entrenadores, safe=False)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # Obtener la escuela del usuario actual
            escuela = Escuela.objects.filter(user=request.user).first()
            if not escuela:
                return JsonResponse({'error': 'Primero debe registrar una escuela'}, status=400)
            
            # Crear el entrenador
            entrenador = Entrenador.objects.create(
                dni_ent=data.get('dni_ent'),
                nombre=data.get('nombre'),
                apellido=data.get('apellido'),
                fecha_nac=data.get('fecha_nac'),
                email=data.get('email', ''),
                telefono=data.get('telefono', ''),
                domicilio=data.get('domicilio', ''),
                periodo_id=data.get('periodo')  # Usar periodo_id para la FK
            )
            
            # Aquí deberías crear la relación en EntDiscEscPer
            # Por ahora solo creamos el entrenador
            return JsonResponse({
                'success': True, 
                'mensaje': 'Entrenador registrado correctamente',
                'dni_ent': entrenador.dni_ent
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def eliminar_entrenador(request, id):
    if request.method == "DELETE":
        try:
            entrenador = Entrenador.objects.get(dni_ent=id)  # Buscar por DNI
            entrenador.delete()
            return JsonResponse({"success": True})
        except Entrenador.DoesNotExist:
            return JsonResponse({"success": False, "error": "No encontrado"}, status=404)



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