import os
from django.core.management.base import BaseCommand
from api.season.models import Season
from api.color.models import Color
from api.relationships.models import SeasonColor


class Command(BaseCommand):
    help = "Create seasons from CSV files and associate colors with them"

    def handle(self, *args, **options):
        # Map season names to their corresponding CSV filenames.
        season_files = {
            "Autumn": "autumn.csv",
            "Spring": "spring.csv",
            "Summer": "summer.csv",
            "Winter": "winter.csv",
        }

        # Determine the directory where this command file is located.
        current_dir = os.path.dirname(os.path.abspath(__file__))

        for season_name, csv_filename in season_files.items():
            csv_path = os.path.join(current_dir, csv_filename)
            if not os.path.exists(csv_path):
                self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
                continue

            # Create (or get) the Season object.
            season, created = Season.objects.get_or_create(name=season_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created season "{season_name}"'))
            else:
                self.stdout.write(f'Season "{season_name}" already exists')

            # Open and process the CSV file.
            with open(csv_path, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines, comments, or lines without a semicolon (the expected delimiter).
                    if not line or line.startswith("#") or ";" not in line:
                        continue

                    parts = line.split(";")
                    if len(parts) != 3:
                        self.stdout.write(
                            self.style.WARNING(f"Invalid color line: {line}")
                        )
                        continue

                    try:
                        r, g, b = [int(part) for part in parts]
                    except ValueError:
                        self.stdout.write(
                            self.style.WARNING(f"Non-integer value in line: {line}")
                        )
                        continue

                    # Format the RGB values as "[R G B]"
                    color_code = f"[{r} {g} {b}]"
                    # Since the CSV does not provide a name for the color, we use the code as its name.
                    color_name = color_code

                    # Create (or get) the Color object.
                    color, color_created = Color.objects.get_or_create(
                        code=color_code, defaults={"name": color_name}
                    )
                    if color_created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Created color {color_code}")
                        )
                    else:
                        # If the color exists but has a different name, update it.
                        if color.name != color_name:
                            color.name = color_name
                            color.save()
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated color {color_code} name to "{color_name}"'
                                )
                            )

                    # Associate the Color with the Season via the through model (SeasonColor).
                    association, assoc_created = SeasonColor.objects.get_or_create(
                        season=season, color=color
                    )
                    if assoc_created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Associated color {color_code} with season "{season_name}"'
                            )
                        )
                    else:
                        self.stdout.write(
                            f'Color {color_code} already associated with season "{season_name}"'
                        )

        self.stdout.write(self.style.SUCCESS("Season creation complete."))
