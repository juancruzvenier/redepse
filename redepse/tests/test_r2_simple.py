import os
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.conf import settings
from apps.escuelas.models import Escuela, Documento
from storages.backends.s3boto3 import S3Boto3Storage
from dotenv import load_dotenv
from pathlib import Path

# test_r2_simple.py (Cambios a aplicar en la función test_upload_to_r2)

from storages.backends.s3boto3 import S3Boto3Storage # Esta ya está importada

# ... dentro de test_upload_to_r2(self):
# ... (Crear usuario, escuela, documento, etc.)

# Storage que devuelve Django (normalmente DefaultStorage)
# Esto sigue siendo DefaultStorage y es lo que quieres evitar.
# django_storage = documento.documento.storage 
# print("Storage Django:", type(django_storage).__name__)

# Reemplazar la obtención del storage por la instanciación directa
# Instanciar el storage que DEBE ser usado, ignorando DefaultStorage cacheado.


class R2FunctionalTest(TestCase):
    """
    Test funcional REAL para Cloudflare R2:
    - Carga .env
    - Verifica credenciales
    - Sube archivo real
    - Verifica existencia en bucket
    - Comprueba storage real (no el proxy DefaultStorage)
    - Usa S3Boto3Storage de django-storages
    - Elimina archivo al terminar
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Forzar carga de .env en tests
        env_path = Path(settings.BASE_DIR) / ".env"
        print(f"\nCargando .env desde: {env_path}")
        load_dotenv(env_path)

    def setUp(self):
        print("\n=== Test Funcional Real R2 ===")

        required_env = [
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_BUCKET_NAME",
            "R2_ENDPOINT_URL",
        ]

        missing = [env for env in required_env if not os.getenv(env)]

        if missing:
            raise RuntimeError(f"❌ Faltan variables de entorno para R2: {missing}")

        print("Variables de entorno cargadas correctamente ✔️")

    @override_settings(DEFAULT_FILE_STORAGE="storages.backends.s3boto3.S3Boto3Storage")
    def test_upload_to_r2(self):
        print("DEFAULT_FILE_STORAGE:", settings.DEFAULT_FILE_STORAGE)

        # Crear usuario y escuela
        user = User.objects.create_user("testuser", "test@example.com", "testpass")
        escuela = Escuela.objects.create(
            nombre_esc="Escuela Test",
            localidad="Test City",
            user=user
        )

        # Archivo de prueba
        content = b"Contenido de prueba para Cloudflare R2"
        file = SimpleUploadedFile("r2_test_file.txt", content)

        # Subida real
        documento = Documento.objects.create(
            id_esc=escuela,
            documento=file,
            tipo="prueba_r2"
        )

        print(f"Archivo guardado como: {documento.documento.name}")

        real_storage = S3Boto3Storage() 
        print("Storage real instanciado:", type(real_storage).__name__)

        # Debe ser S3/R2
        self.assertIsInstance(real_storage, S3Boto3Storage) # Ahora esto pasará

        # Verificar existencia en el bucket usando la instancia real
        exists = real_storage.exists(documento.documento.name)
        print("¿Existe en R2?:", exists)
        self.assertTrue(exists)


        # Obtener URL firmada
        try:
            url = real_storage.url(documento.documento.name)
            print("URL firmada generada:")
            print("   ", url)
        except Exception as e:
            print("⚠️ No se pudo generar URL firmada:", e)

        print("=== Test R2 completado con éxito ===")
