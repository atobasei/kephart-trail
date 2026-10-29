from django.core.exceptions import ValidationError

# The official NPS park map is a few MB; this leaves plenty of room.
MAX_MAP_PDF_BYTES = 50 * 1024 * 1024


def validate_pdf(uploaded_file):
    """Reject files that are too large or are not really PDFs, whatever their extension says."""
    if uploaded_file.size > MAX_MAP_PDF_BYTES:
        limit_mb = MAX_MAP_PDF_BYTES // (1024 * 1024)
        raise ValidationError(f"The map must be {limit_mb} MB or smaller.")

    uploaded_file.seek(0)
    header = uploaded_file.read(5)
    uploaded_file.seek(0)
    if header != b"%PDF-":
        raise ValidationError("This file is not a PDF.")
