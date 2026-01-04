from django.contrib import admin
from django.urls import path
from django.http import HttpResponse


def health_check(request):
    """Health check endpoint for AWS ALB"""
    return HttpResponse("healthy", content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
]
