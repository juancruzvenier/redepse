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
from django.core.files.storage import FileSystemStorage


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
            # === DEBUG: VER SI LLEGAN LOS ARCHIVOS ===
            print("--- INICIO DEBUG FINALIZAR REGISTRO ---")
            print(f"FILES recibidos: {request.FILES.keys()}")
            if 'nota_secretario' in request.FILES:
                print(f"Nota: {request.FILES['nota_secretario'].name} - Size: {request.FILES['nota_secretario'].size}")
            else:
                print("⚠️ NO LLEGÓ nota_secretario en request.FILES")
            
            # Obtener datos del FormData
            datos_json = request.POST.get('datos_json')
            if not datos_json:
                return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400)
                
            datos_completos = json.loads(datos_json)
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
                    estado='pendiente',
                    # AGREGAR ESTAS DOS LÍNEAS:
                    latitud=escuela_data.get('latitud'),   # Recibe el valor o None
                    longitud=escuela_data.get('longitud'), # Recibe el valor o None
                )

                # === ACÁ ESTÁ EL CAMBIO CLAVE ===
                # Configuramos R2 manualmente para forzarlo, igual que en el test
                r2_storage = S3Boto3Storage(
                    access_key=os.getenv('R2_ACCESS_KEY_ID'),
                    secret_key=os.getenv('R2_SECRET_ACCESS_KEY'),
                    bucket_name=os.getenv('R2_BUCKET_NAME'),
                    endpoint_url=os.getenv('R2_ENDPOINT_URL'),
                    region_name='auto',
                    default_acl='private',
                    signature_version='s3v4'
                )

                # 2. GUARDAR ARCHIVOS REALES FORZANDO EL STORAGE
                if 'nota_secretario' in request.FILES:
                    nota_file = request.FILES['nota_secretario']
                    
                    # Creamos la instancia SIN guardar el archivo todavía
                    doc_nota = Documento(
                        id_esc=escuela,
                        tipo='nota_secretario'
                    )
                    # Le inyectamos el storage de R2 al campo
                    doc_nota.documento.storage = r2_storage
                    # Guardamos el archivo manualmente en ese campo
                    doc_nota.documento.save(nota_file.name, nota_file)
                    print(f"✅ Nota secretario subida a R2: {doc_nota.documento.url}")
                
                if 'respaldo_institucional' in request.FILES:
                    respaldo_file = request.FILES['respaldo_institucional']
                    
                    doc_respaldo = Documento(
                        id_esc=escuela,
                        tipo='respaldo_institucional'
                    )
                    doc_respaldo.documento.storage = r2_storage
                    doc_respaldo.documento.save(respaldo_file.name, respaldo_file)
                    print(f"✅ Respaldo subido a R2: {doc_respaldo.documento.url}")

                # 3. Guardar responsable
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
                        print(f"✅ Responsable guardado: {responsable.nombre} {responsable.apellido}")
                    except Exception as e:
                        print(f"❌ Error al guardar responsable: {str(e)}")
                        
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
                
                # 7. Guardar tutores y crear un diccionario para búsqueda rápida
                tutores_dict = {}
                tutores_data = datos_completos.get('tutores', [])
                for tutor_data in tutores_data:
                    tutor = Tutor.objects.create(
                        dni_tutor=tutor_data.get('dni_tutor'),
                        nombre=tutor_data.get('nombre'),
                        apellido=tutor_data.get('apellido'),
                        email=tutor_data.get('email', ''),
                        telefono1=tutor_data.get('telefono1', ''),
                        domicilio=tutor_data.get('domicilio', '')
                    )
                    tutores_dict[tutor_data.get('dni_tutor')] = tutor
                    print(f"✅ Tutor guardado: {tutor.nombre} {tutor.apellido}")
                
                # 8. Guardar alumnos - CORREGIDO: buscar instancia de Tutor
                alumnos_data = datos_completos.get('alumnos', [])
                for alumno_data in alumnos_data:
                    # Obtener la instancia del tutor usando el DNI
                    dni_tutor_str = alumno_data.get('tutor')
                    tutor_instance = None
                    
                    if dni_tutor_str and dni_tutor_str in tutores_dict:
                        tutor_instance = tutores_dict[dni_tutor_str]
                    elif dni_tutor_str:
                        # Intentar buscar el tutor en la base de datos si no está en los recién creados
                        try:
                            tutor_instance = Tutor.objects.get(dni_tutor=dni_tutor_str)
                        except Tutor.DoesNotExist:
                            print(f"⚠️ Tutor con DNI {dni_tutor_str} no encontrado")
                    
                    alumno = Alumno.objects.create(
                        dni_alumno=alumno_data.get('dni_alumno'),
                        nombre=alumno_data.get('nombre'),
                        apellido=alumno_data.get('apellido'),
                        fecha_nac=alumno_data.get('fecha_nac'),
                        domicilio=alumno_data.get('domicilio', ''),
                        dni_tutor=tutor_instance  # ✅ Ahora es una instancia de Tutor, no un string
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
                    
                    print(f"✅ Alumno guardado: {alumno.nombre} {alumno.apellido}")
                
                # 9. Crear solicitud
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