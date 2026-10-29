from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .deletion import delete_account
from .forms import DeleteAccountForm, ProfileForm


@login_required
@require_http_methods(["GET", "POST"])
def account_settings(request):
    user = request.user
    old_avatar_name = user.avatar.name

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            # Remove the old picture file when it's replaced or cleared.
            if old_avatar_name and old_avatar_name != user.avatar.name:
                user.avatar.storage.delete(old_avatar_name)
            messages.success(request, "Your profile was updated.")
            return redirect("accounts:settings")
    else:
        form = ProfileForm(instance=user)

    return render(request, "accounts/settings.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def delete_account_view(request):
    if request.method == "POST":
        form = DeleteAccountForm(request.POST, user=request.user)
        if form.is_valid():
            delete_account(request.user)
            logout(request)
            messages.success(request, "Your account was deleted.")
            return redirect("core:home")
    else:
        form = DeleteAccountForm(user=request.user)

    return render(request, "accounts/delete.html", {"form": form})
