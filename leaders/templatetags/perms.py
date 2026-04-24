"""Template helpers for permission checks.

Usage in templates:
    {% load perms %}
    {% if user|has_perm:"can_manage_memberships" %} ... {% endif %}
    {% if user|has_any_perm:"can_review_endorsements,can_review_market_sellers" %} ... {% endif %}
"""
from django import template
from leaders.permissions import user_has_perm

register = template.Library()


@register.filter(name='has_perm')
def has_perm(user, flag):
    return user_has_perm(user, flag)


@register.filter(name='has_any_perm')
def has_any_perm(user, comma_flags):
    flags = [f.strip() for f in comma_flags.split(',') if f.strip()]
    return any(user_has_perm(user, f) for f in flags)


@register.simple_tag(name='has_perm')
def has_perm_tag(user, flag):
    return user_has_perm(user, flag)
