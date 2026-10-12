from io import BytesIO, StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from .admin import PropertyAdminForm
from .models import StoredImage
from .storage import DatabaseImageStorage


@override_settings(ALLOWED_HOSTS=["testserver"])
class DeploymentTests(TestCase):
    def setUp(self):
        buffer = BytesIO()
        Image.new("RGB", (4, 4), "green").save(buffer, format="PNG")
        self.image_bytes = buffer.getvalue()
        self.storage = DatabaseImageStorage()

    def test_image_survives_new_storage_instance(self):
        name = self.storage.save("properties/test.png", ContentFile(self.image_bytes))
        with DatabaseImageStorage().open(name) as image:
            self.assertEqual(image.read(), self.image_bytes)
        self.assertEqual(self.storage.size(name), len(self.image_bytes))

    def test_public_image_is_served_with_verified_type(self):
        name = self.storage.save("properties/test.png", ContentFile(self.image_bytes))
        response = self.client.get(self.storage.url(name), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.image_bytes)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_missing_image_returns_404(self):
        self.assertEqual(self.client.get("/media/missing.png", secure=True).status_code, 404)

    def test_duplicate_filename_does_not_overwrite(self):
        first = self.storage.save("properties/test.png", ContentFile(self.image_bytes))
        second = self.storage.save("properties/test.png", ContentFile(self.image_bytes))
        self.assertNotEqual(first, second)
        self.assertEqual(StoredImage.objects.count(), 2)

    def test_invalid_image_is_not_saved(self):
        with self.assertRaises(ValidationError):
            self.storage.save("properties/test.png", ContentFile(b"not an image"))
        self.assertFalse(StoredImage.objects.exists())

    @override_settings(MAX_IMAGE_UPLOAD_BYTES=10)
    def test_oversized_image_is_a_form_error(self):
        image = SimpleUploadedFile("test.png", self.image_bytes, content_type="image/png")
        form = PropertyAdminForm(files={"image": image})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)
        self.assertIn("5 MB", str(form.errors["image"]))

    def test_https_redirect_and_public_pages(self):
        response = self.client.get("/health/")
        self.assertRedirects(response, "https://testserver/health/", status_code=301, fetch_redirect_response=False)
        self.assertEqual(self.client.get("/health/", secure=True).content, b"ok")
        self.assertEqual(self.client.get("/", secure=True).status_code, 200)
        self.assertEqual(self.client.get("/admin/login/", secure=True).status_code, 200)

    def test_bootstrap_does_not_reset_existing_password(self):
        first_password = "Example-Initial-Password-4892!"
        with patch.dict("os.environ", {"DJANGO_SUPERUSER_USERNAME": "siteadmin", "DJANGO_SUPERUSER_PASSWORD": first_password}):
            call_command("bootstrap_site", stdout=StringIO())
        with patch.dict("os.environ", {"DJANGO_SUPERUSER_USERNAME": "siteadmin", "DJANGO_SUPERUSER_PASSWORD": "Different-Password-9841!"}):
            call_command("bootstrap_site", stdout=StringIO())
        user = get_user_model().objects.get(username="siteadmin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(first_password))
