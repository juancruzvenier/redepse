from django.shortcuts import render, redirect, get_object_or_404
from formtools.wizard.views import SessionWizardView
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import EscuelaForm, EntrenadorForm, AlumnoForm
from .models import (
    Escuela,
    Entrenador,
    Alumno,
    Periodo,
    EntDiscEscPer,   # <-- NUEVO
    Inscripcion,     # <-- NUEVO
)
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
# Form de entrenadores (paso independiente)
# ---------------------------------------

@login_required
def entrenadores_view(request):
    # Solo permitimos llegar acá si el usuario ya tiene una escuela
    escuela = Escuela.objects.filter(user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")

    form = EntrenadorForm()
    periodos = Periodo.objects.all().order_by("periodo")
    return render(
        request,
        "registro/entrenadores_form.html",
        {"form": form, "periodos": periodos, "escuela": escuela},
    )


@csrf_exempt
@login_required
def entrenadores_api(request):
    if request.method == "GET":
        # Obtener solo los entrenadores de la escuela del usuario actual
        escuela = Escuela.objects.filter(user=request.user).first()
        if escuela:
            # Buscamos los dni_ent asociados a esa escuela en ent_disc_esc_per
            dni_ent_list = EntDiscEscPer.objects.filter(
                id_esc=escuela
            ).values_list("dni_ent", flat=True)

            entrenadores_qs = Entrenador.objects.filter(dni_ent__in=dni_ent_list)

            entrenadores = list(
                entrenadores_qs.values(
                    "dni_ent",
                    "nombre",
                    "apellido",
                    "fecha_nac",
                    "email",
                    "telefono",
                    "domicilio",
                    "periodo",  # o "periodo_id" según tu modelo
                )
            )
        else:
            entrenadores = []
        return JsonResponse(entrenadores, safe=False)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)

            # Obtener la escuela del usuario actual
            escuela = Escuela.objects.filter(user=request.user).first()
            if not escuela:
                return JsonResponse(
                    {"error": "Primero debe registrar una escuela"}, status=400
                )

            # Crear el entrenador
            entrenador = Entrenador.objects.create(
                dni_ent=data.get("dni_ent"),
                nombre=data.get("nombre"),
                apellido=data.get("apellido"),
                fecha_nac=data.get("fecha_nac"),
                email=data.get("email", ""),
                telefono=data.get("telefono", ""),
                domicilio=data.get("domicilio", ""),
                periodo_id=data.get("periodo"),  # Usar periodo_id para la FK
            )

            # Crear la relación en EntDiscEscPer para asociar a la escuela
            EntDiscEscPer.objects.create(
                dni_ent=entrenador,
                id_esc=escuela,
                # Si tu modelo tiene FK como id_periodo:
                id_periodo_id=data.get("periodo"),
                # id_disciplina puede quedar en null por ahora si no lo estás usando
            )

            return JsonResponse(
                {
                    "success": True,
                    "mensaje": "Entrenador registrado correctamente",
                    "dni_ent": entrenador.dni_ent,
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required
def eliminar_entrenador(request, id):
    if request.method == "DELETE":
        try:
            entrenador = Entrenador.objects.get(dni_ent=id)  # Buscar por DNI

            # Eliminamos también las relaciones con escuelas (opcional pero prolijo)
            EntDiscEscPer.objects.filter(dni_ent=entrenador).delete()

            entrenador.delete()
            return JsonResponse({"success": True})
        except Entrenador.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "No encontrado"}, status=404
            )


# ---------------------------------------
# Form de alumnos (paso independiente)
# ---------------------------------------

@login_required
def alumnos_view(request):
    escuela = Escuela.objects.filter(user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")

    form = AlumnoForm()
    periodos = Periodo.objects.all().order_by("periodo")
    return render(
        request,
        "registro/alumnos_form.html",
        {"form": form, "periodos": periodos, "escuela": escuela},
    )


@csrf_exempt
@login_required
def alumnos_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            print("JSON RECIBIDO:", data)   # DEBUG

            escuela = Escuela.objects.filter(user=request.user).first()
            if not escuela:
                return JsonResponse({'error': 'Debe registrar una escuela primero'}, status=400)

            # Crear alumno con tus nuevos campos
            alumno = Alumno.objects.create(
                dni_alumno=data["dni_alumno"],
                nombre=data["nombre"],
                apellido=data["apellido"],
                fecha_nac=data["fecha_nac"],
                domicilio=data.get("domicilio", ""),
                dni_tutor=data.get("dni_tutor")
            )

            # Crear relación con la escuela
            Inscripcion.objects.create(
                dni_alumno=alumno,
                id_esc=escuela
            )

            return JsonResponse({"success": True})

        except Exception as e:
            print("ERROR AL REGISTRAR ALUMNO:", e)
            return JsonResponse({"error": str(e)}, status=400)

    # GET (devolver alumnos)
    elif request.method == "GET":
        escuela = Escuela.objects.filter(user=request.user).first()
        if not escuela:
            return JsonResponse([], safe=False)

        dni_alumnos = Inscripcion.objects.filter(
            id_esc=escuela.id_esc
        ).values_list("dni_alumno", flat=True)

        alumnos = Alumno.objects.filter(dni_alumno__in=dni_alumnos)

        data = [{
            "dni_alumno": a.dni_alumno,
            "nombre": a.nombre,
            "apellido": a.apellido,
            "fecha_nac": str(a.fecha_nac),
            "domicilio": a.domicilio,
            "dni_tutor": a.dni_tutor
        } for a in alumnos]

        return JsonResponse(data, safe=False)



@csrf_exempt
@login_required
def eliminar_alumno(request, id):
    if request.method == "DELETE":
        try:
            alumno = Alumno.objects.get(dni_alumno=id)  # Buscar por DNI

            # Eliminamos también la inscripción en la escuela
            Inscripcion.objects.filter(dni_alumno=alumno).delete()

            alumno.delete()
            return JsonResponse({"success": True})
        except Alumno.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "No encontrado"}, status=404
            )


# ---------------------------------------
# Estado de la solicitud
# ---------------------------------------
@login_required
def estado_solicitud(request):
    escuela = Escuela.objects.filter(user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")
    return render(request, "estado.html", {"escuela": escuela})
