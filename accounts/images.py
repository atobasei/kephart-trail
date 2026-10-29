"""Profile picture processing.

Every upload is re-encoded, which strips EXIF metadata (including GPS location) and gets rid
of anything hidden in the original file. The full image pipeline for post photos comes in
Phase 6; this handles profile pictures only.
"""

from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

AVATAR_SIZE = 256
AVATAR_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
# Refuse absurd dimensions before decoding, so a tiny file can't expand into gigabytes.
MAX_PIXELS = 40_000_000


def process_avatar(uploaded_file):
    """Validate an uploaded image and return a 256×256 JPEG with no metadata."""
    if uploaded_file.size > AVATAR_MAX_UPLOAD_BYTES:
        limit_mb = AVATAR_MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ValidationError(f"Profile pictures must be {limit_mb} MB or smaller.")

    uploaded_file.seek(0)
    try:
        image = Image.open(uploaded_file)
    except (UnidentifiedImageError, OSError) as error:
        raise ValidationError("That file isn't an image we can read.") from error

    # Check the real format from the file's contents, not its extension.
    if image.format not in ALLOWED_FORMATS:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")
    width, height = image.size
    if width * height > MAX_PIXELS:
        raise ValidationError("That image is too large. Try one under 40 megapixels.")

    try:
        image.load()
    except (OSError, Image.DecompressionBombError) as error:
        raise ValidationError("That image couldn't be read. It may be damaged.") from error

    # Phone photos are often stored sideways with an EXIF "rotate me" flag; apply it.
    image = ImageOps.exif_transpose(image)

    # JPEG has no transparency, so put transparent images on a white background.
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")

    # Crop to a centered square, then shrink.
    image = ImageOps.fit(image, (AVATAR_SIZE, AVATAR_SIZE), method=Image.Resampling.LANCZOS)

    output = BytesIO()
    # Saving without passing exif= writes no metadata at all.
    image.save(output, format="JPEG", quality=85, optimize=True)
    return ContentFile(output.getvalue(), name="avatar.jpg")
