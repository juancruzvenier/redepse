from django.test import TestCase

# Create your tests here.
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Probar subida a Backblaze
test_file = default_storage.save('test-backblaze.txt', ContentFile(b'probando backblaze'))
print("✅ Archivo subido:", test_file)
print("📁 Storage backend:", default_storage.__class__.__name__)

# Si es S3, debería mostrar la URL de Backblaze
if hasattr(default_storage, 'url'):
    print("🔗 URL:", default_storage.url(test_file))