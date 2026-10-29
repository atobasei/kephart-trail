from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render


def profile(request, username):
    User = get_user_model()
    profile_user = get_object_or_404(
        User,
        username__iexact=username,
        is_active=True,
        is_deleted=False,
    )
    # /u/SmokyHiker/ and /u/smokyhiker/ are the same person; keep one URL per profile.
    if profile_user.username != username:
        return redirect(profile_user.get_absolute_url(), permanent=True)

    context = {
        "profile_user": profile_user,
    }
    return render(request, "profiles/profile.html", context)
