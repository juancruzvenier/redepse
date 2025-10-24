from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm

# ---------------------------
# Registro de usuario
# ---------------------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Loguear automáticamente al usuario después de registrarse
            login(request, user)
            
            # Redirigir a la página principal
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

# ---------------------------
# Login de usuario
# ---------------------------
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirige a la página principal
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

# ---------------------------
# Logout de usuario
# ---------------------------
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirige al login después de cerrar sesión

# ---------------------------
# Página principal protegida
# ---------------------------
@login_required(login_url='login')
def home_view(request):
    return render(request, 'accounts/home.html', {'user': request.user})
