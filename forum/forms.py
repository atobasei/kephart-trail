from django import forms

from .models import POST_BODY_MAX_LENGTH, THREAD_TITLE_MAX_LENGTH

MARKDOWN_HELP = (
    "**bold**, _italics_, [link text](https://…), - lists, > quotes. "
    f"Up to {POST_BODY_MAX_LENGTH:,} characters."
)


class PostForm(forms.Form):
    body = forms.CharField(
        label="Your post",
        max_length=POST_BODY_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text=MARKDOWN_HELP,
    )


class ThreadForm(forms.Form):
    title = forms.CharField(max_length=THREAD_TITLE_MAX_LENGTH)
    body = forms.CharField(
        label="Your post",
        max_length=POST_BODY_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 10}),
        help_text=MARKDOWN_HELP,
    )
