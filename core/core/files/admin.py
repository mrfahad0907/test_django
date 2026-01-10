from django.contrib import admin

from .models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "original_filename",
        "content_type",
        "file_size",
        "uploaded_by",
        "created_at",
    ]
    list_filter = ["content_type", "created_at"]
    search_fields = ["original_filename", "uploaded_by__email"]
    readonly_fields = ["id", "file_size", "content_type", "created_at", "updated_at"]
    ordering = ["-created_at"]
