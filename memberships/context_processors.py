from .utils import is_president_or_secretary, is_treasurer, user_active_membership


def membership_context(request):
    user = getattr(request, 'user', None)
    return {
        'active_membership': user_active_membership(user) if user else None,
        'is_member': bool(user_active_membership(user)) if user and user.is_authenticated else False,
        'is_treasurer_user': is_treasurer(user) if user else False,
        'is_oversight_user': is_president_or_secretary(user) if user else False,
    }
