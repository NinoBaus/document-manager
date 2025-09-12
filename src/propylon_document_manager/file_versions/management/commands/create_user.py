from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Create a user"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True)
        parser.add_argument("--password", type=str, required=True)
        parser.add_argument("--name", type=str, required=False)

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        name = options.get("name", "")

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR("User with this email already exists"))
            return

        User.objects.create_user(email=email, password=password, name=name)
        self.stdout.write(self.style.SUCCESS(f"User {email} created successfully"))
