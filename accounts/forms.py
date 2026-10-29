from allauth.account.forms import SignupForm as AllauthSignupForm
from django import forms

from core.turnstile import TOKEN_FIELD_NAME, verify_token

from .images import process_avatar
from .models import BIO_MAX_LENGTH, User


class SignupForm(AllauthSignupForm):
    """allauth's signup form plus a server-side Cloudflare Turnstile check."""

    def clean(self):
        cleaned_data = super().clean()
        token = self.data.get(TOKEN_FIELD_NAME, "")
        if not verify_token(token):
            raise forms.ValidationError(
                "We couldn't confirm you're a person. Please try the check again."
            )
        return cleaned_data


class ProfileForm(forms.ModelForm):
    bio = forms.CharField(
        required=False,
        max_length=BIO_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text=f"Optional. Up to {BIO_MAX_LENGTH} characters.",
    )

    class Meta:
        model = User
        fields = ["bio", "avatar"]
        help_texts = {
            "avatar": "Optional. JPEG, PNG, or WebP. It's cropped to a square and location "
            "data is removed.",
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        # Only process a newly uploaded file; leave an existing or cleared picture alone.
        if avatar and hasattr(avatar, "content_type"):
            return process_avatar(avatar)
        return avatar


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        help_text="Enter your password to confirm.",
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("That password is incorrect.")
        return password
