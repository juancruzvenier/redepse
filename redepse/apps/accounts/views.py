from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm
from .models import Escuela
from django.shortcuts import render, get_object_or_404
from redepse.models import Escuela, Entrenador, EntDiscEscPer




# ---------------------------
# Registro
# ---------------------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, 'Cuenta creada con éxito.')
            return redirect('home')
        else:
            messages.error(request, 'Error al crear la cuenta. Verifica los datos ingresados.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

# ---------------------------
# Login
# ---------------------------
from django.contrib.auth.models import User

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')  # tu input "Correo electrónico"
        password = request.POST.get('password')

        # Buscar usuario por correo si existe
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        except User.DoesNotExist:
            username = username_or_email  # intenta como nombre de usuario

        # Autenticar
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username} 👋')

            # 👇👇👇 BLOQUE NUEVO: redirigir según privilegios 👇👇👇
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')  # usuarios con privilegios
            else:
                return redirect('home')  # usuarios normales
            # 👆👆👆 FIN BLOQUE NUEVO 👆👆👆

        else:
            messages.error(request, 'Correo o contraseña incorrectos.')
    else:
        pass  # GET request

    return render(request, 'accounts/login.html')


# ---------------------------
# Logout
# ---------------------------
def logout_view(request):
    logout(request)
    return redirect('login')

# ---------------------------
# Página principal
# ---------------------------
@login_required(login_url='login')
def home_view(request):
    return render(request, 'accounts/home.html', {'user': request.user})

@login_required(login_url='login')
def admin_dashboard(request):
    """Vista de panel solo para usuarios con privilegios."""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    # Traemos todas las escuelas existentes
    escuelas = Escuela.objects.all().order_by('nombre_esc')

    return render(request, 'accounts/admin_dashboard.html', {
        'user': request.user,
        'escuelas': escuelas
    })


def detalle_escuela(request, id_esc):
    escuela = get_object_or_404(Escuela, id_esc=id_esc)
    return render(request, 'accounts/detalle_escuela.html', {'escuela': escuela})

def detalle_escuela(request, id_esc):
    escuela = get_object_or_404(Escuela, id_esc=id_esc)
    entrenadores = Entrenador.objects.filter(
        entdiscescper__id_esc=id_esc
    ).distinct()

    return render(request, 'accounts/detalle_escuela.html', {
        'escuela': escuela,
        'entrenadores': entrenadores
    })
