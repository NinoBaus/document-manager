from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from propylon_document_manager.file_versions.api.views import FileVersionViewSet, FilePermissionsViewSet

if settings.DEBUG:
    router = DefaultRouter(trailing_slash=False)
else:
    router = SimpleRouter(trailing_slash=False)

router.register("file-versions", FileVersionViewSet, basename="file_versions")
router.register("file-permissions", FilePermissionsViewSet, basename="file_permissions")


app_name = "api"
urlpatterns = router.urls
