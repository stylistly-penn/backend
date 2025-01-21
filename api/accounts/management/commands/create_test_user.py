from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.season.models import Season
from api.color.models import Color
from api.relationships.models import SeasonColor


class Command(BaseCommand):
    help = "Create a test user with a season and three warm-tone colors"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Create or get "Test Season"
        season, created = Season.objects.get_or_create(name="Test Season")

        if created:
            self.stdout.write(self.style.SUCCESS('Created "Test Season"'))

        # Assign three warm-tone colors for "Test Season"
        color_codes = [
            "[179 97 71]",  # Deep Terracotta
            "[112 128 79]",  # Muted Olive Green
            "[139 121 94]",  # Warm Taupe
        ]

        for color_code in color_codes:
            color, _ = Color.objects.get_or_create(code=color_code)
            SeasonColor.objects.get_or_create(season=season, color=color)

        # Create test user
        user, created = User.objects.get_or_create(
            username="testuser", defaults={"season": season}
        )

        if created:
            user.set_password("testpassword")
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    'Created test user "testuser" with password "testpassword"'
                )
            )

        self.stdout.write(self.style.SUCCESS("Setup complete!"))
