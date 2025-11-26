import os
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.conf import settings
from apps.escuelas.models import Escuela, Documento
from storages.backends.s3boto3 import S3Boto3Storage
from dotenv import load_dotenv
from pathlib import Path

class R2FunctionalTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cargar variables de entorno
        env_path = Path(settings.BASE_DIR) / ".env"
        load_dotenv(env_path)

    def test_upload_to_r2(self):
        print("\n=== Test Funcional Real R2 (Parchado) ===")

        # 1. Inyectar manualmente las credenciales en settings
        # (Porque settings.py se cargó antes de tener el .env)
        settings.AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
        settings.AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
        settings.AWS_STORAGE_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
        settings.AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')
        settings.AWS_S3_REGION_NAME = 'auto'
        settings.AWS_S3_SIGNATURE_VERSION = 's3v4'

        # 2. Configurar el Storage de R2 explícitamente
        r2_storage = S3Boto3Storage()

        # 3. Parchar el modelo Documento para usar R2 en este test
        field = Documento._meta.get_field('documento')
        original_storage = field.storage # Guardamos el original (local)
        field.storage = r2_storage       # Ponemos el de R2

        try:
            # Crear usuario y escuela
            user = User.objects.create_user("testuser", "test@example.com", "testpass")
            escuela = Escuela.objects.create(
                nombre_esc="Escuela Test", 
                localidad="Test City", 
                user=user
            )

            # Crear archivo y guardar
            content = b"Contenido de prueba para Cloudflare R2"
            file = SimpleUploadedFile("r2_test_file.txt", content)

            print("Subiendo archivo a R2...")
            documento = Documento.objects.create(
                id_esc=escuela,
                documento=file,
                tipo="prueba_r2"
            )

            remote_name = documento.documento.name
            print(f"Archivo subido: {remote_name}")

            # 4. Verificar existencia en R2
            exists = r2_storage.exists(remote_name)
            print(f"¿Existe en el bucket?: {exists}")
            
            self.assertTrue(exists, "El archivo debería existir en R2")

            # Opcional: Imprimir URL
            print(f"URL: {r2_storage.url(remote_name)}")

        except Exception as e:
            print(f"❌ Error durante el test: {e}")
            raise e
