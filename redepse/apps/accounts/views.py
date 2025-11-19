from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
import json

from .forms import RegisterForm, LoginForm
from apps.escuelas.models import (
    Escuela, Entrenador, EntDiscEscPer, Solicitudes,
    Alumno, Inscripcion, Tutor, Disciplina
)

# ====================================================
# 🧩 Registro
# ====================================================
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, 'Cuenta creada con éxito. Por favor, inicia sesión.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Error al crear la cuenta. Verifica los datos ingresados.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


# ====================================================
# 🔐 Login
# ====================================================
def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        # Buscar usuario por correo si existe
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        except User.DoesNotExist:
            username = username_or_email

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username} 👋')
            if user.is_superuser or user.is_staff:
                return redirect('accounts:admin_dashboard')
            else:
                return redirect('escuelas:registro_wizard', paso='escuela')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')

    return render(request, 'accounts/login.html')


# ====================================================
# 🚪 Logout
# ====================================================
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


# ====================================================
# 🏠 Página principal usuario normal
# ====================================================
@login_required(login_url='login')
def home_view(request):
    return render(request, 'accounts/home.html', {'user': request.user})


# ====================================================
# 🧭 Panel de administrador — Escuelas registradas
# ====================================================
@login_required(login_url='login')
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    escuelas_aprobadas_ids = Solicitudes.objects.filter(
        estado__iexact='aprobada'
    ).values_list('id_esc', flat=True)

    escuelas = Escuela.objects.filter(id_esc__in=escuelas_aprobadas_ids).order_by('nombre_esc')

    return render(request, 'accounts/admin_dashboard.html', {
        'user': request.user,
        'escuelas': escuelas
    })


# ====================================================
# 📋 Solicitudes pendientes
# ====================================================
@login_required(login_url='login')
def solicitudes_pendientes(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    ids_pend = Solicitudes.objects.filter(estado__iexact='pendiente') \
                                  .values_list('id_esc', flat=True)
    escuelas = Escuela.objects.filter(id_esc__in=ids_pend).order_by('nombre_esc')

    return render(request, 'accounts/solicitudes_pendientes.html', {'escuelas': escuelas})


# ====================================================
# 🔎 Filtrado de escuelas (AJAX)
# ====================================================
@login_required(login_url='login')
def filtrar_escuelas(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    search = request.GET.get('search', '').strip()
    municipio = request.GET.get('municipio', '').strip()

    escuelas_aprobadas_ids = Solicitudes.objects.filter(
        estado__iexact='aprobada'
    ).values_list('id_esc', flat=True)

    escuelas = Escuela.objects.filter(id_esc__in=escuelas_aprobadas_ids)

    if search:
        escuelas = escuelas.filter(nombre_esc__icontains=search)
    if municipio:
        escuelas = escuelas.filter(localidad__icontains=municipio)

    data = [
        {
            'id_esc': e.id_esc,
            'nombre_esc': e.nombre_esc,
            'email': e.email,
            'telefono1': e.telefono1,
            'telefono2': e.telefono2,
            'localidad': e.localidad,
            'direccion': e.direccion,
            'estado': e.estado,
        }
        for e in escuelas
    ]

    return JsonResponse({'escuelas': data})


# ====================================================
# 🔍 Detalle de escuela (Ver Datos)
# ====================================================
@login_required(login_url='login')
def detalle_escuela(request, id_esc):
    escuela = get_object_or_404(Escuela, id_esc=id_esc)
    origen = request.GET.get('from', 'admin_dashboard')

    entrenadores = Entrenador.objects.filter(entdiscescper__id_esc=id_esc).distinct()
    solicitud = Solicitudes.objects.filter(id_esc=id_esc).first()
    alumnos = Alumno.objects.filter(inscripcion__id_esc=id_esc).distinct()
    tutores = Tutor.objects.filter(
        dni_tutor__in=alumnos.values_list('dni_tutor', flat=True)
    ).distinct()
    disciplinas = Disciplina.objects.filter(
        id_disciplina__in=EntDiscEscPer.objects.filter(id_esc=id_esc).values('id_disciplina')
    ).distinct()

    return render(request, 'accounts/detalle_escuela.html', {
        'escuela': escuela,
        'entrenadores': entrenadores,
        'solicitud': solicitud,
        'alumnos': alumnos,
        'tutores': tutores,
        'disciplinas': disciplinas,
        'origen': origen
    })


# ====================================================
# ✅ Aprobar / Denegar solicitudes (HTML + Logo)
# ====================================================
@csrf_exempt
def gestionar_solicitud(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        id_esc = data.get('id_esc')
        accion = (data.get('accion') or '').strip().lower()
        email = data.get('email')
        mensaje = data.get('mensaje', '')

        escuela = get_object_or_404(Escuela, id_esc=id_esc)
        solicitud = Solicitudes.objects.filter(id_esc=id_esc).first()

        # 🔹 Solo usamos "Aprobada" y "Pendiente" en DB
        if accion == 'aprobar':
            nuevo_estado = 'Aprobada'
            asunto = 'Solicitud Aprobada'
            cuerpo = f"Estimado/a {escuela.nombre_esc}, su solicitud ha sido aprobada."
            texto_html = "Tu solicitud ha sido <b>aprobada ✅</b>."
        elif accion == 'denegar':
            nuevo_estado = 'Pendiente'  # dejamos pendiente para compatibilidad
            asunto = 'Solicitud Rechazada'
            cuerpo = f"Estimado/a {escuela.nombre_esc}, lamentamos informarle que su solicitud ha sido rechazada."
            texto_html = "Tu solicitud ha sido <b>rechazada ❌</b>."
        else:
            return JsonResponse({'error': 'Acción no válida'}, status=400)

        # 🔹 Guardar cambios
        escuela.estado = nuevo_estado
        escuela.save()
        if solicitud:
            solicitud.estado = nuevo_estado
            solicitud.save()

        # 🔹 Crear correo HTML
        html_body = f"""
        <html>
        <body style="font-family:'Poppins',sans-serif; background:#f4f6fa; padding:30px;">
          <div style="max-width:600px; margin:auto; background:#fff; border-radius:12px;
                      box-shadow:0 4px 20px rgba(0,0,0,0.1); overflow:hidden;">
            <div style="background:linear-gradient(90deg,#0066ff,#ff0040); padding:15px; text-align:center;">
              <img src="https://i.postimg.cc/yDYcGvHd/logo-redepse.png" 
              alt="REDEPSE" style="height:60px;">
            </div>
            <div style="padding:25px;">
              <h2 style="color:#0066ff;">{asunto}</h2>
              <p>Hola <b>{escuela.nombre_esc}</b>,</p>
              <p>{texto_html}</p>
              {f"<p><b>Observaciones:</b> {mensaje}</p>" if mensaje else ""}
              <br>
              <p style="font-size:14px; color:#666;">Saludos,<br><b>Equipo REDEPSE</b></p>
            </div>
          </div>
        </body>
        </html>
        """

        # 🔹 Enviar correo
        try:
            email_message = EmailMultiAlternatives(
                subject=asunto,
                body=cuerpo,
                from_email='admin@redepse.com',
                to=[email],
            )
            email_message.attach_alternative(html_body, "text/html")
            email_message.send(fail_silently=False)
        except Exception as e:
            print(f"⚠️ Error enviando correo: {e}")

        return JsonResponse({'status': 'ok', 'mensaje': f'Solicitud {asunto.lower()} con éxito'})

    except Exception as e:
        print(f"❌ Error en gestionar_solicitud: {e}")
        return JsonResponse({'error': 'Error procesando la solicitud'}, status=500)

