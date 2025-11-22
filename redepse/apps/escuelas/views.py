from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from .forms import *
from .models import *
from django.db import transaction
import json
import os
import base64
from django.core.files.base import ContentFile
from django.utils import timezone


@method_decorator(login_required, name='dispatch')
class RegistroWizardView(TemplateView):
    template_name = "registro/wizard_base.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        pasos = [
            {'nombre': 'Datos de la Escuela', 'url': 'escuela', 'numero': 1},
            {'nombre': 'Documentación', 'url': 'documentacion', 'numero': 2},
            {'nombre': 'Disciplinas', 'url': 'disciplinas', 'numero': 3},
            {'nombre': 'Entrenadores', 'url': 'entrenadores', 'numero': 4},
            {'nombre': 'Tutores', 'url': 'tutores', 'numero': 5},
            {'nombre': 'Alumnos', 'url': 'alumnos', 'numero': 6},
            {'nombre': 'Finalizar Registro', 'url': 'finalizar', 'numero': 7},
        ]
        
        paso_actual = self.kwargs.get('paso', 'escuela')
        context['pasos'] = pasos
        context['paso_actual'] = paso_actual
        context['paso_numero'] = next((p['numero'] for p in pasos if p['url'] == paso_actual), 1)
        context['total_pasos'] = len(pasos)
        
        # ✅ AGREGAR DISCIPLINAS AL CONTEXTO PARA EL PASO 3
        if paso_actual == 'disciplinas':
            context['disciplinas'] = Disciplina.objects.all()
        
        # Cargar datos del localStorage para prellenar formularios
        storage_key = f're-depse_escuela_registro_{self.request.user.id}'
        datos_guardados = self.request.session.get(storage_key, {})
        context['datos_guardados'] = datos_guardados
        
        return context
    
    def get_template_names(self):
        paso_actual = self.kwargs.get('paso', 'escuela')
        return [f"registro/paso_{paso_actual}.html"]

@login_required
def guardar_paso(request, paso):
    if request.method == 'POST':
        storage_key = f're-depse_escuela_registro_{request.user.id}'
        datos_guardados = request.session.get(storage_key, {})
        
        if paso == 'escuela':
            form = EscuelaForm(request.POST)
            if form.is_valid():
                datos_guardados['escuela'] = form.cleaned_data
                request.session[storage_key] = datos_guardados
                return JsonResponse({'success': True, 'message': 'Datos de escuela guardados'})
        
        elif paso == 'documentacion':
            # El archivo se manejará en el frontend con localStorage
            datos_guardados['documentacion'] = {'completado': True}
            request.session[storage_key] = datos_guardados
            return JsonResponse({'success': True, 'message': 'Documentación guardada'})
        
        elif paso == 'disciplinas':
            disciplinas_ids = request.POST.getlist('disciplinas')
            datos_guardados['disciplinas'] = {
                'ids': disciplinas_ids,
                'nombres': list(Disciplina.objects.filter(id_disciplina__in=disciplinas_ids).values_list('disciplina', flat=True))
            }
            request.session[storage_key] = datos_guardados
            return JsonResponse({'success': True, 'message': 'Disciplinas guardadas'})
        
        return JsonResponse({'success': False, 'errors': 'Datos inválidos'})
    
    return JsonResponse({'success': False, 'errors': 'Método no permitido'})

@login_required
def finalizar_registro(request):
    if request.method == 'POST':
        try:
            storage_key = f're-depse_escuela_registro_{request.user.id}'
            datos_completos = request.session.get(storage_key, {})
            
            if not datos_completos:
                return JsonResponse({'success': False, 'error': 'No hay datos para guardar'})
            
            with transaction.atomic():
                # 1. Crear escuela
                escuela_data = datos_completos.get('escuela', {})
                escuela = Escuela.objects.create(
                    **escuela_data,
                    solicitud_enviada=True,
                    user=request.user,
                    estado='pendiente'
                )
                
                # 2. Guardar disciplinas seleccionadas
                disciplinas_data = datos_completos.get('disciplinas', {})
                if disciplinas_data.get('ids'):
                    for disciplina_id in disciplinas_data['ids']:
                        EntDiscEscPer.objects.create(
                            id_esc=escuela,
                            id_disciplina_id=disciplina_id,
                            id_periodo=Periodo.objects.filter(periodo=2025).first() or Periodo.objects.first()
                        )
                
                # 3. Guardar entrenadores
                entrenadores_data = datos_completos.get('entrenadores', [])
                for entrenador_data in entrenadores_data:
                    entrenador = Entrenador.objects.create(**entrenador_data)
                    EntDiscEscPer.objects.create(
                        dni_ent=entrenador,
                        id_esc=escuela,
                        id_periodo=Periodo.objects.filter(periodo=2025).first() or Periodo.objects.first()
                    )
                
                # 4. Guardar tutores
                tutores_data = datos_completos.get('tutores', [])
                for tutor_data in tutores_data:
                    Tutor.objects.create(**tutor_data)
                
                # 5. Guardar alumnos
                alumnos_data = datos_completos.get('alumnos', [])
                for alumno_data in alumnos_data:
                    alumno = Alumno.objects.create(
                        dni_alumno=alumno_data['dni_alumno'],
                        nombre=alumno_data['nombre'],
                        apellido=alumno_data['apellido'],
                        fecha_nac=alumno_data['fecha_nac'],
                        domicilio=alumno_data.get('domicilio', ''),
                        dni_tutor=alumno_data.get('tutor')
                    )
                    Inscripcion.objects.create(
                        dni_alumno=alumno,
                        id_esc=escuela
                    )
                    # Asociar disciplina si está disponible
                    if alumno_data.get('disciplina'):
                        AluDiscEscPer.objects.create(
                            dni_alumno=alumno,
                            id_disciplina_id=alumno_data['disciplina'],
                            id_esc=escuela,
                            id_periodo=Periodo.objects.filter(periodo=2025).first() or Periodo.objects.first()
                        )
                
                # 6. Crear solicitud
                Solicitudes.objects.create(
                    id_esc=escuela,
                    estado='Pendiente'
                )
            
            # Limpiar sesión
            del request.session[storage_key]
            
            return JsonResponse({'success': True, 'message': 'Solicitud enviada exitosamente'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

'''
@csrf_exempt
@login_required
def finalizar_registro(request):
    if request.method == 'POST':
        try:
            datos_completos = json.loads(request.body)
            print("Datos recibidos:", datos_completos)
            
            with transaction.atomic():
                # 1. Crear escuela
                escuela_data = datos_completos.get('escuela', {})
                escuela = Escuela.objects.create(
                    nombre_esc=escuela_data.get('nombre_esc'),
                    localidad=escuela_data.get('localidad'),
                    direccion=escuela_data.get('direccion'),
                    email=escuela_data.get('email'),
                    telefono1=escuela_data.get('telefono1'),
                    solicitud_enviada=True,
                    user=request.user,
                    estado='pendiente'
                )
                
                # 2. Guardar documento si existe
                documentacion_data = datos_completos.get('documentacion')
                if documentacion_data:
                    try:
                        # Decodificar base64
                        file_data = base64.b64decode(documentacion_data['datos'])
                        file_name = documentacion_data['nombre']
                        
                        # Crear archivo para Django
                        file_content = ContentFile(file_data, name=file_name)
                        
                        # Guardar documento
                        Documento.objects.create(
                            id_esc=escuela,
                            documento=file_content,
                            tipo='nota_secretario',
                            fecha_subida=timezone.now()
                        )
                        print(f"Documento guardado: {file_name}")
                    except Exception as e:
                        print(f"Error al guardar documento: {str(e)}")
                        # No romper el flujo por error en documento
                
                # Obtener periodo actual
                from datetime import datetime
                año_actual = datetime.now().year
                
                try:
                    periodo = Periodo.objects.get(periodo=año_actual)
                except Periodo.DoesNotExist:
                    periodo = Periodo.objects.create(periodo=año_actual)
                
                # 3. Guardar disciplinas seleccionadas
                disciplinas_data = datos_completos.get('disciplinas', {})
                if disciplinas_data.get('ids'):
                    for disciplina_id in disciplinas_data['ids']:
                        EntDiscEscPer.objects.create(
                            id_esc=escuela,
                            id_disciplina_id=disciplina_id,
                            id_periodo=periodo
                        )
                
                # 4. Guardar entrenadores
                entrenadores_data = datos_completos.get('entrenadores', [])
                for entrenador_data in entrenadores_data:
                    entrenador = Entrenador.objects.create(
                        dni_ent=entrenador_data.get('dni_ent'),
                        nombre=entrenador_data.get('nombre'),
                        apellido=entrenador_data.get('apellido'),
                        fecha_nac=entrenador_data.get('fecha_nac'),
                        email=entrenador_data.get('email', ''),
                        telefono=entrenador_data.get('telefono', ''),
                        domicilio=entrenador_data.get('domicilio', ''),
                        periodo=periodo
                    )
                    EntDiscEscPer.objects.create(
                        dni_ent=entrenador,
                        id_esc=escuela,
                        id_periodo=periodo
                    )
                
                # 5. Guardar tutores
                tutores_data = datos_completos.get('tutores', [])
                for tutor_data in tutores_data:
                    Tutor.objects.create(
                        dni_tutor=tutor_data.get('dni_tutor'),
                        nombre=tutor_data.get('nombre'),
                        apellido=tutor_data.get('apellido'),
                        email=tutor_data.get('email', ''),
                        telefono1=tutor_data.get('telefono1', ''),
                        domicilio=tutor_data.get('domicilio', '')
                    )
                
                # 6. Guardar alumnos
                alumnos_data = datos_completos.get('alumnos', [])
                for alumno_data in alumnos_data:
                    alumno = Alumno.objects.create(
                        dni_alumno=alumno_data.get('dni_alumno'),
                        nombre=alumno_data.get('nombre'),
                        apellido=alumno_data.get('apellido'),
                        fecha_nac=alumno_data.get('fecha_nac'),
                        domicilio=alumno_data.get('domicilio', ''),
                        dni_tutor=alumno_data.get('tutor')
                    )
                    
                    Inscripcion.objects.create(
                        dni_alumno=alumno,
                        id_esc=escuela
                    )
                    
                    if alumno_data.get('disciplina'):
                        AluDiscEscPer.objects.create(
                            dni_alumno=alumno,
                            id_disciplina_id=alumno_data['disciplina'],
                            id_esc=escuela,
                            id_periodo=periodo
                        )
                
                # 7. Crear solicitud
                solicitud = Solicitudes.objects.create(
                    id_esc=escuela,
                    estado='Pendiente'
                )
            
            return JsonResponse({
                'success': True, 
                'message': 'Solicitud enviada exitosamente',
                'escuela_id': escuela.id_esc
            })
            
        except Exception as e:
            print(f"Error al guardar: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
'''

@csrf_exempt
@login_required
def finalizar_registro(request):
    if request.method == 'POST':
        try:
            datos_completos = json.loads(request.body)
            print("Datos recibidos:", datos_completos)
            
            with transaction.atomic():
                # 1. Crear escuela
                escuela_data = datos_completos.get('escuela', {})
                escuela = Escuela.objects.create(
                    nombre_esc=escuela_data.get('nombre_esc'),
                    localidad=escuela_data.get('localidad'),
                    direccion=escuela_data.get('direccion'),
                    email=escuela_data.get('email'),
                    telefono1=escuela_data.get('telefono1'),
                    solicitud_enviada=True,
                    user=request.user,
                    estado='pendiente'
                )
                
                # 2. Guardar documento si existe
                documentacion_data = datos_completos.get('documentacion')
                if documentacion_data:
                    try:
                        # Decodificar base64
                        file_data = base64.b64decode(documentacion_data['datos'])
                        file_name = documentacion_data['nombre']
                        
                        # Crear archivo para Django
                        file_content = ContentFile(file_data, name=file_name)
                        
                        # Guardar documento
                        Documento.objects.create(
                            id_esc=escuela,
                            documento=file_content,
                            tipo='nota_secretario',
                            fecha_subida=timezone.now()
                        )
                        print(f"Documento guardado: {file_name}")
                    except Exception as e:
                        print(f"Error al guardar documento: {str(e)}")
                        # No romper el flujo por error en documento

                # Obtener periodo actual - CORREGIDO: usar id_periodo
                from datetime import datetime
                año_actual = datetime.now().year
                
                # Buscar o crear periodo usando id_periodo
                try:
                    periodo = Periodo.objects.get(id_periodo=año_actual)
                except Periodo.DoesNotExist:
                    # Si no existe, crear con id_periodo = año_actual
                    periodo = Periodo.objects.create(id_periodo=año_actual)
                
                # 2. Guardar disciplinas seleccionadas
                disciplinas_data = datos_completos.get('disciplinas', {})
                if disciplinas_data.get('ids'):
                    for disciplina_id in disciplinas_data['ids']:
                        EntDiscEscPer.objects.create(
                            id_esc=escuela,
                            id_disciplina_id=disciplina_id,
                            id_periodo=periodo  # ← CORREGIDO
                        )
                
                # 3. Guardar entrenadores - CORREGIDO
                entrenadores_data = datos_completos.get('entrenadores', [])
                for entrenador_data in entrenadores_data:
                    entrenador = Entrenador.objects.create(
                        dni_ent=entrenador_data.get('dni_ent'),
                        nombre=entrenador_data.get('nombre'),
                        apellido=entrenador_data.get('apellido'),
                        fecha_nac=entrenador_data.get('fecha_nac'),
                        email=entrenador_data.get('email', ''),
                        telefono=entrenador_data.get('telefono', ''),
                        domicilio=entrenador_data.get('domicilio', ''),
                        periodo=periodo  # ← CORREGIDO: usar objeto periodo, no id
                    )
                    # Crear relación entrenador-escuela-disciplina
                    EntDiscEscPer.objects.create(
                        dni_ent=entrenador,
                        id_esc=escuela,
                        id_periodo=periodo  # ← CORREGIDO
                    )
                
                # 4. Guardar tutores
                tutores_data = datos_completos.get('tutores', [])
                for tutor_data in tutores_data:
                    Tutor.objects.create(
                        dni_tutor=tutor_data.get('dni_tutor'),
                        nombre=tutor_data.get('nombre'),
                        apellido=tutor_data.get('apellido'),
                        email=tutor_data.get('email', ''),
                        telefono1=tutor_data.get('telefono1', ''),
                        domicilio=tutor_data.get('domicilio', '')
                    )
                
                # 5. Guardar alumnos
                alumnos_data = datos_completos.get('alumnos', [])
                for alumno_data in alumnos_data:
                    alumno = Alumno.objects.create(
                        dni_alumno=alumno_data.get('dni_alumno'),
                        nombre=alumno_data.get('nombre'),
                        apellido=alumno_data.get('apellido'),
                        fecha_nac=alumno_data.get('fecha_nac'),
                        domicilio=alumno_data.get('domicilio', ''),
                        dni_tutor=alumno_data.get('dni_tutor')
                    )
                    
                    # Crear relación alumno-escuela
                    Inscripcion.objects.create(
                        dni_alumno=alumno,
                        id_esc=escuela
                    )
                    
                    # Crear relación alumno-disciplina-escuela-periodo
                    if alumno_data.get('disciplina'):
                        AluDiscEscPer.objects.create(
                            dni_alumno=alumno,
                            id_disciplina_id=alumno_data['disciplina'],
                            id_esc=escuela,
                            id_periodo=periodo  # ← CORREGIDO
                        )
                
                # 6. Crear solicitud con estado 'Pendiente'
                solicitud = Solicitudes.objects.create(
                    id_esc=escuela,
                    estado='Pendiente'
                )
            
            return JsonResponse({
                'success': True, 
                'message': 'Solicitud enviada exitosamente',
                'escuela_id': escuela.id_esc
            })
            
        except Exception as e:
            print(f"Error al guardar: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def estado_solicitud(request):
    escuela = Escuela.objects.filter(user=request.user).first()
    if not escuela:
        return redirect("escuelas:wizard")
    return render(request, "registro/estado.html", {"escuela": escuela})  # ← Cambiar la ruta