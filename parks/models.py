from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_pdf

# GSMNP is the flagship park and lives at /gsmnp/ instead of /parks/<slug>/.
FLAGSHIP_PARK_SLUG = "gsmnp"

# Section slugs share the URL space under /gsmnp/ with these fixed paths.
RESERVED_SECTION_SLUGS = {"trails", "t"}


class Park(models.Model):
    class Kind(models.TextChoices):
        NATIONAL = "national", "National park"
        STATE = "state", "State park"

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.NATIONAL)
    description = models.TextField(blank=True)
    map_pdf = models.FileField(
        "park map (PDF)",
        upload_to="maps/",
        blank=True,
        validators=[FileExtensionValidator(["pdf"]), validate_pdf],
    )
    uses_sections = models.BooleanField(
        default=True,
        help_text="Group trails into sections on the park page. State parks usually don't.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.is_flagship:
            return reverse("parks:gsmnp")
        return reverse("parks:park_detail", kwargs={"park_slug": self.slug})

    @property
    def is_flagship(self):
        return self.slug == FLAGSHIP_PARK_SLUG


class Section(models.Model):
    park = models.ForeignKey(Park, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers come first. Sections with the same number are sorted A–Z.",
    )

    class Meta:
        ordering = ["park", "sort_order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["park", "slug"], name="unique_section_slug_per_park"),
            models.UniqueConstraint(fields=["park", "name"], name="unique_section_name_per_park"),
        ]

    def __str__(self):
        return f"{self.name} ({self.park.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.park.is_flagship:
            return reverse("parks:gsmnp_section", kwargs={"section_slug": self.slug})
        return reverse(
            "parks:section_detail",
            kwargs={"park_slug": self.park.slug, "section_slug": self.slug},
        )

    def clean(self):
        if self.slug in RESERVED_SECTION_SLUGS:
            raise ValidationError({"slug": f'"{self.slug}" is reserved for site URLs.'})


class Trail(models.Model):
    park = models.ForeignKey(Park, on_delete=models.CASCADE, related_name="trails")
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trails",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160)
    length_miles = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="One-way length in miles.",
    )
    description = models.TextField(blank=True)
    # The one-to-one link to the trail's thread is added in Phase 3 with the Thread model.

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["park", "slug"], name="unique_trail_slug_per_park"),
            models.UniqueConstraint(fields=["park", "name"], name="unique_trail_name_per_park"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.park.is_flagship:
            return reverse("parks:gsmnp_trail", kwargs={"trail_slug": self.slug})
        return reverse(
            "parks:trail_detail",
            kwargs={"park_slug": self.park.slug, "trail_slug": self.slug},
        )

    def clean(self):
        if self.section_id is not None and self.park_id is not None:
            if self.section.park_id != self.park_id:
                raise ValidationError({"section": "This section belongs to a different park."})


class Board(models.Model):
    """A place for threads. "General" has no park; each park gets one board."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    park = models.OneToOneField(
        Park,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="board",
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
