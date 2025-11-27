from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = "accounts"

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('filtrar_escuelas/', views.filtrar_escuelas, name='filtrar_escuelas'),
    path('solicitudes_pendientes/', views.solicitudes_pendientes, name='solicitudes_pendientes'),
    path('gestionar_solicitud/', views.gestionar_solicitud, name='gestionar_solicitud'),
    path('entrenadores/', views.entrenadores_registrados, name='entrenadores_registrados'),

    # 👉 esta es la vista para el modal con los datos
    path('escuela/<int:id_esc>/', views.detalle_escuela, name='detalle_escuela'),
    path('activar/<uidb64>/<token>/', views.activate_account, name='activate'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(
    template_name='accounts/password_reset_form.html',
    email_template_name='accounts/password_reset_email.txt',  # texto simple (fallback)
    html_email_template_name='accounts/password_reset_email.html',  # HTML renderizado
    subject_template_name='accounts/password_reset_subject.txt',
    success_url=reverse_lazy('accounts:password_reset_done'),
), name='password_reset'),
path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
    template_name='accounts/password_reset_done.html',
), name='password_reset_done'),
path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
    template_name='accounts/password_reset_confirm.html',
    success_url=reverse_lazy('accounts:password_reset_complete'),
), name='password_reset_confirm'),
path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
    template_name='accounts/password_reset_complete.html',
), name='password_reset_complete'),

path('enviar-capacitacion/', views.enviar_capacitacion, name='enviar_capacitacion'),
path('reenviar-activacion/', views.reenviar_activacion, name='reenviar_activacion'),


]
