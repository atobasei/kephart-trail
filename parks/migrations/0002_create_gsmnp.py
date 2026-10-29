from django.db import migrations

GSMNP_DESCRIPTION = (
    "Over 800 miles of trail across the Tennessee and North Carolina line, "
    "from Cades Cove to Big Creek. Trails are grouped by section below."
)


def create_gsmnp(apps, schema_editor):
    """GSMNP is the only park at launch. Its trails are loaded with `manage.py import_trails`."""
    Park = apps.get_model("parks", "Park")
    Park.objects.get_or_create(
        slug="gsmnp",
        defaults={
            "name": "Great Smoky Mountains National Park",
            "kind": "national",
            "uses_sections": True,
            "description": GSMNP_DESCRIPTION,
        },
    )


def remove_gsmnp(apps, schema_editor):
    Park = apps.get_model("parks", "Park")
    Park.objects.filter(slug="gsmnp").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("parks", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_gsmnp, remove_gsmnp),
    ]
