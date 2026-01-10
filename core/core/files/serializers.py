from rest_framework import serializers

from .models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for listing and retrieving files."""

    download_url = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = [
            "id",
            "original_filename",
            "content_type",
            "file_size",
            "file_url",
            "download_url",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "content_type",
            "file_size",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload."""

    file = serializers.FileField(
        help_text="The file to upload",
        allow_empty_file=False,
    )

    def validate_file(self, value):
        # Optional: Add file size validation
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size // (1024 * 1024)}MB"
            )
        return value

    def create(self, validated_data):
        file = validated_data["file"]
        user = self.context["request"].user if self.context["request"].user.is_authenticated else None

        uploaded_file = UploadedFile(
            original_filename=file.name,
            content_type=file.content_type or "application/octet-stream",
            file_size=file.size,
            uploaded_by=user,
        )
        uploaded_file.save()
        uploaded_file.file.save(file.name, file, save=True)

        return uploaded_file
