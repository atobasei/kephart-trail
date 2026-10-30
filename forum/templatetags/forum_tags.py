from django import template

from forum.rules import can_delete_post, can_edit_post

register = template.Library()


@register.filter
def editable_by(post, user):
    return can_edit_post(user, post)


@register.filter
def deletable_by(post, user):
    return can_delete_post(user, post)
