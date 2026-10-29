"""Load trails from a CSV file so trail data lives in the repo and is reviewed in pull requests.

The CSV needs a header row with these columns:

    park,section,name,length_miles

- park: the park's slug (the park must already exist, e.g. "gsmnp").
- section: section name. Created if it doesn't exist yet. Leave blank for parks without sections.
- name: the trail name.
- length_miles: one-way length in miles. Optional.

Running the command again is safe: trails are matched by park and name, then updated.
Trails that are in the database but missing from the CSV are left alone and listed in the output.
"""

import csv
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from parks.models import Park, Section, Trail

REQUIRED_COLUMNS = ["park", "section", "name", "length_miles"]


class DryRunRollback(Exception):
    """Raised to roll back the transaction at the end of a dry run."""


class Command(BaseCommand):
    help = "Create or update trails (and their sections) from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to the trails CSV, e.g. data/trails/gsmnp.csv")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Check the file and report what would change, without saving anything.",
        )

    def handle(self, *args, **options):
        rows = self.read_rows(options["csv_path"])

        try:
            with transaction.atomic():
                summary = self.import_rows(rows)
                if options["dry_run"]:
                    raise DryRunRollback()
        except DryRunRollback:
            self.stdout.write(self.style.WARNING("Dry run: nothing was saved."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Sections created: {summary['sections_created']}. "
                f"Trails created: {summary['trails_created']}, "
                f"updated: {summary['trails_updated']}, "
                f"unchanged: {summary['trails_unchanged']}."
            )
        )
        for trail in summary["trails_not_in_csv"]:
            self.stdout.write(f"In the database but not in the CSV (left alone): {trail.name}")

    def read_rows(self, csv_path):
        try:
            # utf-8-sig drops the byte-order mark Excel adds when saving as CSV.
            with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
                reader = csv.DictReader(csv_file)
                missing_columns = []
                for column in REQUIRED_COLUMNS:
                    if reader.fieldnames is None or column not in reader.fieldnames:
                        missing_columns.append(column)
                if missing_columns:
                    raise CommandError(f"Missing CSV columns: {', '.join(missing_columns)}")

                rows = []
                for row in reader:
                    row["line_number"] = reader.line_num
                    rows.append(row)
                return rows
        except FileNotFoundError as error:
            raise CommandError(f"File not found: {csv_path}") from error

    def import_rows(self, rows):
        summary = {
            "sections_created": 0,
            "trails_created": 0,
            "trails_updated": 0,
            "trails_unchanged": 0,
            "trails_not_in_csv": [],
        }
        parks_by_slug = {}
        names_seen_per_park = {}

        for row in rows:
            line = row["line_number"]
            park_slug = (row["park"] or "").strip()
            section_name = (row["section"] or "").strip()
            trail_name = (row["name"] or "").strip()

            if not park_slug:
                raise CommandError(f"Line {line}: park is empty.")
            if not trail_name:
                raise CommandError(f"Line {line}: name is empty.")

            if park_slug not in parks_by_slug:
                try:
                    parks_by_slug[park_slug] = Park.objects.get(slug=park_slug)
                except Park.DoesNotExist as error:
                    raise CommandError(
                        f'Line {line}: no park with slug "{park_slug}". Add it in the admin first.'
                    ) from error
                names_seen_per_park[park_slug] = set()
            park = parks_by_slug[park_slug]

            if trail_name in names_seen_per_park[park_slug]:
                raise CommandError(f'Line {line}: "{trail_name}" appears more than once.')
            names_seen_per_park[park_slug].add(trail_name)

            length_miles = self.parse_length(row["length_miles"], line)
            section = self.get_or_create_section(park, section_name, line, summary)
            self.save_trail(park, section, trail_name, length_miles, line, summary)

        for park_slug, park in parks_by_slug.items():
            names_in_csv = names_seen_per_park[park_slug]
            for trail in park.trails.order_by("name"):
                if trail.name not in names_in_csv:
                    summary["trails_not_in_csv"].append(trail)

        return summary

    def parse_length(self, raw_value, line):
        raw_value = (raw_value or "").strip()
        if raw_value == "":
            return None
        try:
            return Decimal(raw_value)
        except InvalidOperation as error:
            raise CommandError(
                f'Line {line}: length_miles "{raw_value}" is not a number.'
            ) from error

    def get_or_create_section(self, park, section_name, line, summary):
        if section_name == "":
            return None

        section = park.sections.filter(name=section_name).first()
        if section is not None:
            return section

        # New sections go at the end; existing sort_order values set in the admin are kept.
        section = Section(park=park, name=section_name, slug=slugify(section_name))
        self.validate(section, line)
        section.save()
        summary["sections_created"] += 1
        return section

    def save_trail(self, park, section, trail_name, length_miles, line, summary):
        trail = park.trails.filter(name=trail_name).first()
        if trail is None:
            trail = Trail(
                park=park,
                section=section,
                name=trail_name,
                slug=slugify(trail_name),
                length_miles=length_miles,
            )
            self.validate(trail, line)
            trail.save()
            summary["trails_created"] += 1
            return

        # Compare section ids so a missing section on both sides counts as unchanged.
        new_section_id = None
        if section is not None:
            new_section_id = section.id

        if trail.section_id == new_section_id and trail.length_miles == length_miles:
            summary["trails_unchanged"] += 1
            return

        trail.section = section
        trail.length_miles = length_miles
        self.validate(trail, line)
        trail.save()
        summary["trails_updated"] += 1

    def validate(self, obj, line):
        try:
            obj.full_clean()
        except ValidationError as error:
            messages = []
            for field, field_errors in error.message_dict.items():
                messages.append(f"{field}: {' '.join(field_errors)}")
            raise CommandError(f"Line {line}: {'; '.join(messages)}") from error
