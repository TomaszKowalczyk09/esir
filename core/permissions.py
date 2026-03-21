from functools import wraps

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect


def has_any_role(user, roles):
    if not getattr(user, "is_authenticated", False):
        return False
    return getattr(user, "rola", None) in set(roles)


def is_prezydium(user):
    return has_any_role(user, {"prezydium"})


def is_radny_like(user):
    return has_any_role(user, {"radny", "administrator", "prezydium"})


def can_manage_session(user):
    return has_any_role(user, {"prezydium", "administrator"})


def is_prezydium_or_admin(user):
    return has_any_role(user, {"prezydium", "administrator"})


def require_roles(*roles, on_fail="forbidden", redirect_to="panel", message="Brak uprawnień"):
    """Centralny dekorator autoryzacji oparty o role biznesowe.

    on_fail:
    - "forbidden": HttpResponseForbidden
    - "redirect": redirect(redirect_to)
    - "json": JsonResponse({"error": message}, status=403)
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if has_any_role(request.user, roles):
                return view_func(request, *args, **kwargs)

            if on_fail == "redirect":
                return redirect(redirect_to)
            if on_fail == "json":
                return JsonResponse({"error": message}, status=403)
            return HttpResponseForbidden(message)

        return wrapper

    return decorator


def require_manage_session(on_fail="forbidden", redirect_to="panel"):
    return require_roles(
        "prezydium",
        "administrator",
        on_fail=on_fail,
        redirect_to=redirect_to,
    )


def require_prezydium_only(on_fail="forbidden", redirect_to="panel"):
    return require_roles(
        "prezydium",
        on_fail=on_fail,
        redirect_to=redirect_to,
    )


def require_prezydium_or_admin(on_fail="forbidden", redirect_to="panel"):
    return require_roles(
        "prezydium",
        "administrator",
        on_fail=on_fail,
        redirect_to=redirect_to,
    )


def require_radny_like(on_fail="forbidden", redirect_to="panel"):
    return require_roles(
        "radny",
        "administrator",
        "prezydium",
        on_fail=on_fail,
        redirect_to=redirect_to,
    )
