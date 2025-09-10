import os
import hashlib
import re

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .managers import UserManager


def validate_path(value):
    if not value:
        return value

    pattern = r'^[a-zA-Z0-9/_-]+$'
    if not re.match(pattern, value):
        raise ValidationError("Path can only contain letters, numbers, /, _, and -")
    if ".." in value or "//" in value:
        raise ValidationError("Invalid path structure.")
    return value


class User(AbstractUser):
    """
    Default custom user model for Propylon Document Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


def user_directory_path(instance, filename):
    path = f'{str(instance.user.id)}/{instance.path}'
    return os.path.join(path, filename)


class FileVersion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="file_versions"
    )
    file = models.FileField(upload_to=user_directory_path)
    file_name = models.CharField(max_length=512)
    path = models.CharField(max_length=1024, validators=[validate_path], blank=True)
    revision = models.IntegerField(default=1)
    content_hash = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("path", "revision", "user")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.content_hash and self.file:
            sha256 = hashlib.sha256()
            for chunk in self.file.chunks():
                sha256.update(chunk)
            self.content_hash = sha256.hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file_name} (v{self.revision}) by {self.user.email}"


class FilePermissions(models.Model):
    READ = "read"
    READ_WRITE = "read_write"
    PERMISSION_CHOICES = [
        (READ, "Read"),
        (READ_WRITE, "Read / Write"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="file_permissions"
    )
    file = models.ForeignKey(
        FileVersion,
        on_delete=models.CASCADE,
        related_name="file_permissions"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_file_permissions"
    )
    permissions = models.CharField(max_length=10, choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = ("user", "file", "permissions")
