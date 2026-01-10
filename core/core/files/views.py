import os
import uuid

from django.conf import settings
from django.http import FileResponse
from django.http import Http404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class FileUploadView(APIView):
    """
    Upload a file to media directory.

    POST /api/files/upload/
    """

    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate unique filename
        ext = os.path.splitext(file.name)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"

        # Save to media/files/
        upload_dir = os.path.join(settings.MEDIA_ROOT, "files")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Build download URL
        download_url = request.build_absolute_uri(f"/api/files/download/{unique_filename}/")

        return Response(
            {
                "message": "File uploaded successfully",
                "filename": unique_filename,
                "original_filename": file.name,
                "size": file.size,
                "download_url": download_url,
            },
            status=status.HTTP_201_CREATED,
        )


class FileDownloadView(APIView):
    """
    Download a file from media directory.

    GET /api/files/download/{filename}/
    """

    permission_classes = [AllowAny]

    def get(self, request, filename):
        file_path = os.path.join(settings.MEDIA_ROOT, "files", filename)

        if not os.path.exists(file_path):
            raise Http404("File not found")

        response = FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=filename,
        )
        return response


class FileListView(APIView):
    """
    List all files in media directory.

    GET /api/files/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        upload_dir = os.path.join(settings.MEDIA_ROOT, "files")

        if not os.path.exists(upload_dir):
            return Response({"files": []})

        files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "download_url": request.build_absolute_uri(f"/api/files/download/{filename}/"),
                })

        return Response({"files": files})
