import uuid

from django.conf import settings
from django.db import models


def file_upload_path(instance, filename):
    """Generate upload path for files: media/files/<uuid>/<filename>"""
    return f"files/{instance.id}/{filename}"


class UploadedFile(models.Model):
    """Model for storing uploaded files."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_files",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Uploaded File"
        verbose_name_plural = "Uploaded Files"

    def __str__(self):
        return self.original_filename

    @property
    def download_url(self):
        """Return the download URL for this file."""
        return f"/api/files/{self.id}/download/"
