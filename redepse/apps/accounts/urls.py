from django.urls import path
from . import views
from .views import register_view, login_view, logout_view, home_view, admin_dashboard

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    
    # 👉 esta es la vista para el modal con los datos
    path('escuela/<int:id_esc>/', views.detalle_escuela, name='detalle_escuela'),

]
