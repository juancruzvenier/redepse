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
from storages.backends.s3boto3 import S3Boto3Storage


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


@csrf_exempt
@login_required
def finalizar_registro(request):
    if request.method == 'POST':
        try:
            # Obtener datos del JSON del body (no de session)
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

                # 2. Guardar responsable
                if escuela_data.get('dni_resp'):
                    try:
                        responsable, created = Responsable.objects.get_or_create(
                            dni_resp=escuela_data.get('dni_resp'),
                            defaults={
                                'nombre': escuela_data.get('resp_nombre'),
                                'apellido': escuela_data.get('resp_apellido'),
                                'email': escuela_data.get('resp_email'),
                                'telefono1': escuela_data.get('resp_telefono1'),
                            }
                        )
                        # Opcional: Asignar responsable a la escuela si tu modelo tiene la FK
                        # escuela.dni_resp = responsable
                        # escuela.save()
                        print(f"✅ Responsable guardado: {responsable.nombre} {responsable.apellido}")
                    except Exception as e:
                        print(f"❌ Error al guardar responsable: {str(e)}")
                
                # 3. Guardar documentos
                documentacion_data = datos_completos.get('documentacion')
                if documentacion_data:
                    # Guardar nota al secretario
                    if documentacion_data.get('nota_secretario'):
                        try:
                            nota_data = documentacion_data['nota_secretario']
                            file_data = base64.b64decode(nota_data['datos'])
                            file_name = f"nota_secretario_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{nota_data['nombre']}"
                            
                            file_content = ContentFile(file_data, name=file_name)
                            Documento.objects.create(
                                id_esc=escuela,
                                documento=file_content,
                                tipo='nota_secretario'
                            )
                            print(f"✅ Nota secretario subida: {file_name}")
                        except Exception as e:
                            print(f"❌ Error al subir nota secretario: {str(e)}")
                    
                    # Guardar respaldo institucional
                    if documentacion_data.get('respaldo_institucional'):
                        try:
                            respaldo_data = documentacion_data['respaldo_institucional']
                            file_data = base64.b64decode(respaldo_data['datos'])
                            file_name = f"respaldo_institucional_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{respaldo_data['nombre']}"
                            
                            file_content = ContentFile(file_data, name=file_name)
                            Documento.objects.create(
                                id_esc=escuela,
                                documento=file_content,
                                tipo='respaldo_institucional'
                            )
                            print(f"✅ Respaldo institucional subido: {file_name}")
                        except Exception as e:
                            print(f"❌ Error al subir respaldo institucional: {str(e)}")

                # 4. Obtener periodo actual
                from datetime import datetime
                año_actual = datetime.now().year
                
                try:
                    periodo = Periodo.objects.get(periodo=año_actual)
                except Periodo.DoesNotExist:
                    periodo = Periodo.objects.create(periodo=año_actual)
                
                # 5. Guardar disciplinas seleccionadas
                disciplinas_data = datos_completos.get('disciplinas', {})
                if disciplinas_data.get('ids'):
                    for disciplina_id in disciplinas_data['ids']:
                        EntDiscEscPer.objects.create(
                            id_esc=escuela,
                            id_disciplina_id=disciplina_id,
                            id_periodo=periodo
                        )
                
                # 6. Guardar entrenadores
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
                
                # 7. Guardar tutores
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
                
                # 8. Guardar alumnos
                alumnos_data = datos_completos.get('alumnos', [])
                for alumno_data in alumnos_data:
                    alumno = Alumno.objects.create(
                        dni_alumno=alumno_data.get('dni_alumno'),
                        nombre=alumno_data.get('nombre'),
                        apellido=alumno_data.get('apellido'),
                        fecha_nac=alumno_data.get('fecha_nac'),
                        domicilio=alumno_data.get('domicilio', ''),
                        dni_tutor=alumno_data.get('tutor')  # Asegurate que este campo existe
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
                
                # 9. Crear solicitud
                solicitud = Solicitudes.objects.create(
                    id_esc=escuela,
                    estado='Pendiente'
                )
            
            # Limpiar localStorage del frontend (se maneja desde el JavaScript)
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
        return redirect("escuelas:registro_wizard", paso='escuela')
    
    # Obtener entrenadores a través de la tabla intermedia
    entrenadores_ids = EntDiscEscPer.objects.filter(
        id_esc=escuela
    ).values_list('dni_ent', flat=True)
    entrenadores = Entrenador.objects.filter(dni_ent__in=entrenadores_ids)
    
    # Obtener alumnos a través de la tabla intermedia
    alumnos_ids = Inscripcion.objects.filter(
        id_esc=escuela
    ).values_list('dni_alumno', flat=True)
    alumnos = Alumno.objects.filter(dni_alumno__in=alumnos_ids)
    
    # Obtener la solicitud
    solicitud = Solicitudes.objects.filter(id_esc=escuela).first()
    
    context = {
        'escuela': escuela,
        'entrenadores': entrenadores,
        'alumnos': alumnos,
        'solicitud': solicitud,
    }
    
    return render(request, "registro/estado.html", context)


# Crear storage manualmente
def get_storage():
    if os.getenv('B2_ACCESS_KEY'):
        return S3Boto3Storage(
            access_key=os.getenv('B2_ACCESS_KEY'),
            secret_key=os.getenv('B2_SECRET_KEY'),
            bucket_name=os.getenv('B2_BUCKET_NAME'),
            endpoint_url=os.getenv('B2_ENDPOINT'),
        )
    else:
        from django.core.files.storage import default_storage
        return default_storage