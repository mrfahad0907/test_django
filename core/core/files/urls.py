from django.urls import path

from .views import FileDownloadView
from .views import FileListView
from .views import FileUploadView

urlpatterns = [
    path("", FileListView.as_view(), name="file-list"),
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("download/<str:filename>/", FileDownloadView.as_view(), name="file-download"),
]
