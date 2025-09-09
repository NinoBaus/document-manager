from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from propylon_document_manager.file_versions.api.views import FileVersionViewSet, RegisterView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("file-versions", FileVersionViewSet, basename="file_versions")
router.register("register", RegisterView)


app_name = "api"
urlpatterns = router.urls
