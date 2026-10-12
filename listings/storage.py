from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.files.storage import Storage
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from PIL import Image, UnidentifiedImageError

from .models import StoredImage


@deconstructible
class DatabaseImageStorage(Storage):
    """将小型房源图片保存在 PostgreSQL，适用于免费演示部署。"""

    def _open(self, name, mode="rb"):
        try:
            image = StoredImage.objects.get(pk=name)
        except StoredImage.DoesNotExist as error:
            raise FileNotFoundError(name) from error
        return File(BytesIO(bytes(image.content)), name=name)

    def _save(self, name, content):
        content.seek(0)
        data = content.read(settings.MAX_IMAGE_UPLOAD_BYTES + 1)
        if len(data) > settings.MAX_IMAGE_UPLOAD_BYTES:
            raise ValidationError("房源图片不能超过 5 MB。")
        try:
            with Image.open(BytesIO(data)) as image:
                content_type = Image.MIME.get(image.format)
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise ValidationError("请上传有效的图片文件。") from error
        if not content_type or content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            raise ValidationError("仅支持 JPG、PNG、WebP 和 GIF 图片。")
        StoredImage.objects.create(name=name, content=data, content_type=content_type)
        return name

    def exists(self, name):
        return StoredImage.objects.filter(pk=name).exists()

    def size(self, name):
        return len(StoredImage.objects.only("content").get(pk=name).content)

    def url(self, name):
        return reverse("cloud_media", kwargs={"name": name})

    def delete(self, name):
        StoredImage.objects.filter(pk=name).delete()
