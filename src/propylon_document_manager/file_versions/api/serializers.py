from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Max
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
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


class FilePermissionsSerializer(serializers.ModelSerializer):
    user = serializers.CharField()
    file = serializers.PrimaryKeyRelatedField(queryset=FileVersion.objects.all())
    permissions = serializers.ChoiceField(FilePermissions.PERMISSION_CHOICES)

    class Meta:
        model = FilePermissions
        fields = ["id", "user", "file", "permissions", 'owner']
        read_only_fields = ['owner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["file"].queryset = FileVersion.objects.filter(user=request.user)

    def validate_user(self, value):
        try:
            return User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

    def create(self, validated_data):
        request = self.context["request"]
        owner = request.user
        if validated_data["file"].user != owner:
            raise serializers.ValidationError("You are not the Owner of selected object.")

        if validated_data["file"].user == validated_data["user"]:
            raise serializers.ValidationError("You are trying to add File permissions to the Owner.")
        validated_data["owner"] = owner
        return super().create(validated_data)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        if User.objects.filter(email=validated_data["email"]).exists():
            raise serializers.ValidationError("User already exists")

        adapter = get_adapter()
        user = adapter.new_user(request=self.context.get("request"))
        user.email = validated_data["email"]
        user.name = validated_data.get("name", "")
        user.set_password(validated_data["password"])
        user.save()
        setup_user_email(self.context.get("request"), user, [])
        return user


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
