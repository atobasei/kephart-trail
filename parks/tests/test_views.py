import pytest
from django.core.files.base import ContentFile

from parks.models import Park, Section, Trail


@pytest.fixture
def gsmnp_with_trails():
    gsmnp = Park.objects.get(slug="gsmnp")
    cosby = Section.objects.create(park=gsmnp, name="Cosby", slug="cosby", sort_order=2)
    abrams = Section.objects.create(
        park=gsmnp, name="Abrams Creek", slug="abrams-creek", sort_order=1
    )
    Trail.objects.create(park=gsmnp, section=cosby, name="Snake Den Ridge Trail", length_miles=5.3)
    Trail.objects.create(park=gsmnp, section=cosby, name="Gabes Mountain Trail")
    Trail.objects.create(park=gsmnp, section=abrams, name="Rabbit Creek Trail")
    return gsmnp


@pytest.mark.django_db
def test_home_links_to_gsmnp(client):
    response = client.get("/")

    assert b'href="/gsmnp/"' in response.content


@pytest.mark.django_db
def test_park_page_lists_sections_in_order_and_trails_a_to_z(client, gsmnp_with_trails):
    response = client.get("/gsmnp/")

    assert response.status_code == 200
    html = response.content.decode()
    assert html.index("Abrams Creek") < html.index("Cosby")
    assert html.index("Gabes Mountain Trail") < html.index("Snake Den Ridge Trail")
    assert "5.3 mi" in html


@pytest.mark.django_db
def test_park_page_shows_map_download_only_when_uploaded(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    gsmnp = Park.objects.get(slug="gsmnp")

    response = client.get("/gsmnp/")
    assert b"Download park map" not in response.content

    gsmnp.map_pdf.save("gsmnp-map.pdf", ContentFile(b"%PDF-1.7\n"))
    response = client.get("/gsmnp/")
    assert b"Download park map" in response.content
    assert b"/media/maps/gsmnp-map" in response.content


@pytest.mark.django_db
def test_section_page_lists_only_its_trails(client, gsmnp_with_trails):
    response = client.get("/gsmnp/cosby/")

    assert response.status_code == 200
    assert b"Snake Den Ridge Trail" in response.content
    assert b"Rabbit Creek Trail" not in response.content


@pytest.mark.django_db
def test_trail_page(client, gsmnp_with_trails):
    response = client.get("/gsmnp/trails/snake-den-ridge-trail/")

    assert response.status_code == 200
    assert b"Snake Den Ridge Trail" in response.content
    assert b"Latest conditions" in response.content
    assert b'href="/gsmnp/cosby/"' in response.content


@pytest.mark.django_db
def test_unknown_section_and_trail_are_404(client, gsmnp_with_trails):
    assert client.get("/gsmnp/not-a-section/").status_code == 404
    assert client.get("/gsmnp/trails/not-a-trail/").status_code == 404


@pytest.mark.django_db
def test_gsmnp_under_parks_redirects_to_its_own_url(client, gsmnp_with_trails):
    response = client.get("/parks/gsmnp/trails/rabbit-creek-trail/")

    assert response.status_code == 301
    assert response["Location"] == "/gsmnp/trails/rabbit-creek-trail/"


@pytest.mark.django_db
def test_state_park_without_sections_lists_trails_a_to_z(client):
    park = Park.objects.create(
        name="Frozen Head State Park", kind=Park.Kind.STATE, uses_sections=False
    )
    Trail.objects.create(park=park, name="Panther Branch Trail")
    Trail.objects.create(park=park, name="Chimney Top Trail")

    response = client.get("/parks/frozen-head-state-park/")

    assert response.status_code == 200
    html = response.content.decode()
    assert html.index("Chimney Top Trail") < html.index("Panther Branch Trail")
    assert client.get("/parks/frozen-head-state-park/trails/chimney-top-trail/").status_code == 200
