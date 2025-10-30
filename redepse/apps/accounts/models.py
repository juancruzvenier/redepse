from django.db import models
from django.contrib.auth.models import User

'''
class Escuela(models.Model):
    id_esc = models.AutoField(primary_key=True)
    nombre_esc = models.CharField(max_length=150)
    email = models.EmailField(max_length=100)
    telefono1 = models.CharField(max_length=50)
    telefono2 = models.CharField(max_length=50, blank=True, null=True)
    localidad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    estado = models.CharField(max_length=50)
    solicitud_enviada = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    

    class Meta:
        db_table = 'escuela'  # 👈 usa tu tabla real

    def __str__(self):
        return self.nombre_esc
'''