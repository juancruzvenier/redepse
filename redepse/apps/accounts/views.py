from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm

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
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

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
            return redirect('home')
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
