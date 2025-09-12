import os
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from propylon_document_manager.file_versions.models import FileVersion

User = get_user_model()

file_versions = [
    'bill_document',
    'amendment_document',
    'act_document',
    'statute_document',
]

class Command(BaseCommand):
    help = "Load basic file version fixtures"

    def _create_test_user(self, file_name):
        user, created = User.objects.get_or_create(
            email=f'{file_name}@example.com',
            defaults={
                "name": file_name,
            },
        )
        if created:
            user.set_password(f'{file_name}123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user {user.email}"))

        return user

    def handle(self, *args, **options):
        base_path = os.path.join(settings.BASE_DIR, "fixtures")

        for file_name in file_versions:
            user = self._create_test_user(file_name)

            file_path = os.path.join(base_path, file_name)

            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f"File {file_path} does not exist, skipping"))
                continue

            with open(file_path, "rb") as f:
                obj, created = FileVersion.objects.get_or_create(
                    file_name=file_name,
                    revision=1,
                    user=user,
                    defaults={"file": File(f, name=file_name)}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created {file_name} owned by {user.email}"))
                else:
                    self.stdout.write(self.style.WARNING(f"{file_name} already exists"))

        self.stdout.write(
            self.style.SUCCESS("Finished loading test users and file versions")
        )
