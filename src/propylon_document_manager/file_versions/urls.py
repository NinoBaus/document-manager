from django.urls import path
from propylon_document_manager.file_versions.api import views

urlpatterns = [
    path("auth-token/", views.EmailAuthToken.as_view(), name="auth-token"),
    path("cas/<str:hash_value>", views.FileCASView.as_view(), name="file_cas"),
    path("dir/<path:file_path>", views.FileServeView.as_view(), name="serve_file"),
]
