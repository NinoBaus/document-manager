from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.contrib.auth import authenticate
from django.urls import reverse

from ..models import FileVersion, FilePermissions

User = get_user_model()


class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "file_name", "revision", "content_hash"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user
        validated_data["file_name"] = validated_data["file"].name
        validated_data["revision"] = self.get_revision(validated_data)

        return super().create(validated_data)

    @staticmethod
    def get_revision(validated_data):
        user = validated_data['user']
        file_name = validated_data["file_name"]
        path = validated_data["path"]

        existing_versions = FileVersion.objects.filter(user=user, file_name=file_name, path=path)
        if not existing_versions.exists():
            return 1

        latest_version = existing_versions.aggregate(Max("revision"))["revision__max"] or 0
        return latest_version + 1

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        request = self.context.get("request")

        folder_path = ''
        if instance.path:
            folder_path = f'{instance.path}/'

        file_path = f"{folder_path}{instance.file_name}?revision={instance.revision}"
        url = reverse("serve_file", kwargs={"file_path": file_path})
        if request:
            ret["file"] = request.build_absolute_uri(url)
        else:
            ret["file"] = url

        return ret


class ShareFileSerializer(serializers.Serializer):
    email = serializers.EmailField()
    permission = serializers.ChoiceField(choices=FilePermissions.PERMISSION_CHOICES)


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
        else:
            raise serializers.ValidationError("Must include email and password.")

        attrs["user"] = user
        return attrs
