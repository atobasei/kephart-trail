from django.contrib import admin

from .models import Board, Park, Section, Trail


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ["name", "slug", "sort_order"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Park)
class ParkAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "kind", "uses_sections", "has_map"]
    list_filter = ["kind", "uses_sections"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [SectionInline]

    @admin.display(boolean=True, description="Map")
    def has_map(self, park):
        return bool(park.map_pdf)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["name", "park", "sort_order", "slug"]
    list_editable = ["sort_order"]
    list_filter = ["park"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Trail)
class TrailAdmin(admin.ModelAdmin):
    list_display = ["name", "section", "park", "length_miles"]
    list_filter = ["park", "section"]
    list_select_related = ["section", "park"]
    search_fields = ["name", "slug", "section__name"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["section"]


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "park"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
