import os
import logging
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from django.conf import settings

logger = logging.getLogger(__name__)

class BackblazeService:
    def __init__(self):
        self.account_id = settings.B2_ACCOUNT_ID
        self.application_key = settings.B2_APPLICATION_KEY
        self.bucket_name = settings.B2_BUCKET_NAME
        self.api = None
        self.bucket = None
        self._authenticate()

    def _authenticate(self):
        """Autenticar con Backblaze B2"""
        try:
            info = InMemoryAccountInfo()
            self.api = B2Api(info)
            self.api.authorize_account("production", self.account_id, self.application_key)
            self.bucket = self.api.get_bucket_by_name(self.bucket_name)
            logger.info("Autenticación con Backblaze B2 exitosa")
        except Exception as e:
            logger.error(f"Error autenticando con Backblaze B2: {str(e)}")
            raise

    def upload_file(self, file_data, file_name, content_type=None):
        """
        Subir archivo a Backblaze B2
        
        Args:
            file_data: Bytes del archivo
            file_name: Nombre del archivo
            content_type: Tipo MIME del archivo
        
        Returns:
            dict: Información del archivo subido
        """
        try:
            if content_type is None:
                content_type = 'application/octet-stream'

            # Subir archivo
            uploaded_file = self.bucket.upload_bytes(
                file_data,
                file_name,
                content_type=content_type
            )

            # Obtener URL de descarga
            download_url = self.api.get_download_url_for_fileid(uploaded_file.id_)
            
            logger.info(f"Archivo {file_name} subido exitosamente a Backblaze")
            
            return {
                'file_id': uploaded_file.id_,
                'file_name': uploaded_file.file_name,
                'download_url': download_url,
                'content_type': uploaded_file.content_type,
                'size': uploaded_file.size
            }
            
        except Exception as e:
            logger.error(f"Error subiendo archivo a Backblaze B2: {str(e)}")
            raise

    def delete_file(self, file_id):
        """Eliminar archivo de Backblaze B2"""
        try:
            self.api.delete_file_version(file_id, file_id)
            logger.info(f"Archivo {file_id} eliminado de Backblaze")
        except Exception as e:
            logger.error(f"Error eliminando archivo de Backblaze B2: {str(e)}")
            raise

# Instancia global del servicio
backblaze_service = BackblazeService()