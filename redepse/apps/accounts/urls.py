from django.urls import path
from . import views

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

    # 👉 esta es la vista para el modal con los datos
    path('escuela/<int:id_esc>/', views.detalle_escuela, name='detalle_escuela'),

]
