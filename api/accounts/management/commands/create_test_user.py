from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.season.models import Season
from api.color.models import Color
from api.relationships.models import SeasonColor


class Command(BaseCommand):
    help = "Create a test user with a season and three warm-tone colors, and ensure testuser is an all access admin"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Create or update test user
        user, created = User.objects.get_or_create(
            username="testuser",
            defaults={"is_staff": True, "is_superuser": True},
        )

        if created:
            user.set_password("testpassword")
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    'Created test user "testuser" with password "testpassword"'
                )
            )
        else:
            # Ensure the user is marked as staff and superuser
            updated = False
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if updated:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Updated "testuser" to have full admin privileges.'
                    )
                )

        self.stdout.write(self.style.SUCCESS("Setup complete!"))
