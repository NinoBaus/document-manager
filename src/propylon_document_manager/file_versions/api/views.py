from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.db.models import Q

from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import FileVersion, FilePermissions
from .serializers import FileVersionSerializer, EmailAuthTokenSerializer, FilePermissionsSerializer
from propylon_document_manager.utils.permissions import FileVersionPermission

User = get_user_model()


class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet, CreateModelMixin, DestroyModelMixin):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, FileVersionPermission]
    serializer_class = FileVersionSerializer

    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user

        owned_files = Q(user=user)
        permitted_files = Q(file_permissions__user=user)

        queryset = FileVersion.objects.filter(owned_files | permitted_files).distinct()
        return queryset


class FilePermissionsViewSet(ModelViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FilePermissionsSerializer

    def get_queryset(self):
        return FilePermissions.objects.filter(owner=self.request.user)


class EmailAuthToken(ObtainAuthToken):
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class FileServeView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, file_path):
        revision = request.query_params.get("revision")
        path, file_name = self.get_file_path_and_name(file_path)

        owned_files = Q(user=request.user)
        permitted_files = Q(file_permissions__user=request.user)
        qs = FileVersion.objects.filter(owned_files | permitted_files).filter(path=path, file_name=file_name)

        if not qs.exists():
            return Response({"error": "file not found"}, status=404)

        if revision is not None:
            file_obj = qs.filter(revision=int(revision)).first()
            if not file_obj:
                return Response({"error": "revision not found"}, status=404)
        else:
            file_obj = qs.order_by("-revision").first()

        response = FileResponse(file_obj.file.open("rb"))
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response

    def get_file_path_and_name(self, file_path):
        folders = file_path.split('/')
        file = folders.pop()
        path = '/'.join(folders)
        return path, file


class FileCASView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, hash_value):
        owned_files = Q(user=request.user)
        permitted_files = Q(file_permissions__user=request.user)
        files = FileVersion.objects.filter(owned_files | permitted_files).filter(content_hash=hash_value)
        if not files.exists():
            return Response({"error": "No files found with this hash"}, status=404)
        serializer = FileVersionSerializer(files, many=True, context={"request": request})
        return Response(serializer.data)
