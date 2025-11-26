from django.db import models
from django.contrib.auth.models import User

class Documento(models.Model):
    TIPOS_DOCUMENTO = [
        ('nota_secretario', 'Nota al Secretario'),
        ('respaldo_institucional', 'Respaldo Institucional'),
    ]
    
    id_documento = models.AutoField(primary_key=True)
    id_esc = models.ForeignKey('Escuela', models.DO_NOTHING, db_column='id_esc')
    documento = models.FileField(upload_to='documentos/%Y/%m/%d/')
    tipo = models.CharField(max_length=50, choices=TIPOS_DOCUMENTO)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documentos'

# Tus otros modelos permanecen igual...

class AluDiscEscPer(models.Model):
    dni_alumno = models.ForeignKey('Alumno', models.DO_NOTHING, db_column='dni_alumno', blank=True, null=True)
    id_disciplina = models.ForeignKey('Disciplina', models.DO_NOTHING, db_column='id_disciplina', blank=True, null=True)
    id_esc = models.ForeignKey('Escuela', models.DO_NOTHING, db_column='id_esc', blank=True, null=True)
    id_periodo = models.ForeignKey('Periodo', models.DO_NOTHING, db_column='id_periodo', blank=True, null=True)

    class Meta:
        db_table = 'alu_disc_esc_per'


class Alumno(models.Model):
    dni_alumno = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    fecha_nac = models.DateField()
    domicilio = models.CharField(max_length=100, blank=True, null=True)
    dni_tutor = models.ForeignKey('Tutor', models.DO_NOTHING, db_column='dni_tutor', blank=True, null=True)

    class Meta:
        db_table = 'alumno'



class Capacitacion(models.Model):
    id_capacitacion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha = models.DateField(blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'capacitaciones'


class Disciplina(models.Model):
    id_disciplina = models.AutoField(primary_key=True)
    disciplina = models.CharField(max_length=50)

    class Meta:
        db_table = 'disciplina'


class Empleado(models.Model):
    dni_emp = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    domicilio = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100)
    id_user = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'empleado'


class EntDiscEscPer(models.Model):
    dni_ent = models.ForeignKey('Entrenador', models.DO_NOTHING, db_column='dni_ent', blank=True, null=True)
    id_disciplina = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='id_disciplina', blank=True, null=True)
    id_esc = models.ForeignKey('Escuela', models.DO_NOTHING, db_column='id_esc', blank=True, null=True)
    id_periodo = models.ForeignKey('Periodo', models.DO_NOTHING, db_column='id_periodo', blank=True, null=True)

    class Meta:
        db_table = 'ent_disc_esc_per'


class Entrenador(models.Model):
    dni_ent = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    domicilio = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)  # ✔ AHORA EXISTE
    fecha_nac = models.DateField()
    periodo = models.ForeignKey(
        'Periodo',
        models.DO_NOTHING,
        db_column='periodo',  # ✔ columna de tu BD real
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'entrenador'



class Escuela(models.Model):
    id_esc = models.AutoField(primary_key=True)
    nombre_esc = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    telefono1 = models.CharField(max_length=20)
    telefono2 = models.CharField(max_length=20, blank=True, null=True)
    localidad = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    solicitud_enviada = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    dni_resp = models.ForeignKey('Responsable', models.DO_NOTHING, db_column='dni_resp', null=True, blank=True)

    class Meta:
        db_table = 'escuela'


class Inscripcion(models.Model):
    pk = models.CompositePrimaryKey('dni_alumno', 'id_esc')
    dni_alumno = models.ForeignKey(Alumno, models.DO_NOTHING, db_column='dni_alumno')
    id_esc = models.ForeignKey(Escuela, models.DO_NOTHING, db_column='id_esc')

    class Meta:
        db_table = 'inscripcion'


class Participacion(models.Model):
    pk = models.CompositePrimaryKey('dni_ent', 'id_capacitacion')
    dni_ent = models.ForeignKey(Entrenador, models.DO_NOTHING, db_column='dni_ent')
    id_capacitacion = models.ForeignKey(Capacitacion, models.DO_NOTHING, db_column='id_capacitacion')
    estado = models.CharField(max_length=20, blank=True, null=True)
    fecha_participacion = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'participacion'


class Periodo(models.Model):
    periodo = models.IntegerField(primary_key=True, unique=True)

    class Meta:
        db_table = 'periodo'


class Responsable(models.Model):
    dni_resp = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    telefono1 = models.CharField(max_length=20)
    telefono2 = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'responsable'


class Solicitudes(models.Model):
    id_solicitud = models.AutoField(primary_key=True)
    id_esc = models.ForeignKey(Escuela, models.DO_NOTHING, db_column='id_esc')
    estado = models.CharField(max_length=9, blank=True, null=True)

    class Meta:
        db_table = 'solicitudes'


class Tutor(models.Model):
    dni_tutor = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    domicilio = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100)
    telefono1 = models.CharField(max_length=20)
    telefono2 = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'tutor'


class Usuario(models.Model):
    id_user = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=50)
    email = models.CharField(unique=True, max_length=100)
    contraseña = models.CharField(unique=True, max_length=30)
    rol = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        db_table = 'usuarios'
