from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_safe

from .models import StoredImage


@require_safe
def cloud_media(request, name):
    image = get_object_or_404(StoredImage, pk=name)
    response = HttpResponse(bytes(image.content), content_type=image.content_type)
    response["Cache-Control"] = "public, max-age=86400"
    response["X-Content-Type-Options"] = "nosniff"
    return response
