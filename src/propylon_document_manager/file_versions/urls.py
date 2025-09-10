from django.urls import path
from propylon_document_manager.file_versions.api import views

urlpatterns = [
    path("api/auth-token", views.EmailAuthToken.as_view(), name="auth-token"),
    path("api/cas/<str:hash_value>", views.FileCASView.as_view(), name="file_cas"),
    path("api/dir/<path:file_path>", views.FileServeView.as_view(), name="serve_file"),
]
