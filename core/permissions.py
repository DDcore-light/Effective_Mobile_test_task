from rest_framework import exceptions, permissions

from access_control.models import AccessRule

# Соответствие HTTP-метода полю разрешения "своих" / "всех" объектов.
METHOD_TO_PERMISSION_FIELDS = {
    "GET": ("read_permission", "read_all_permission"),
    "POST": ("create_permission", "create_permission"),
    "PUT": ("update_permission", "update_all_permission"),
    "PATCH": ("update_permission", "update_all_permission"),
    "DELETE": ("delete_permission", "delete_all_permission"),
}


class IsAuthenticated(permissions.BasePermission):
    """
    Простая проверка "пользователь залогинен" — используется там, где
    доступ не зависит от ролевой матрицы (например, операции над
    собственным профилем: обновление данных, logout, удаление аккаунта).
    """

    message = "Требуется аутентификация."

    def has_permission(self, request, view):
        user = request.user
        if user is None or not getattr(user, "is_authenticated", False):
            raise exceptions.NotAuthenticated("Требуется аутентификация.")
        return True


class ResourcePermission(permissions.BasePermission):
    """
    Универсальный permission-класс, реализующий ролевую систему доступа
    из ТЗ (roles / business_elements / access_roles_rules).

    Каждый View должен объявить атрибут `business_element = "<имя>"`,
    соответствующий записи в таблице business_elements.

    Логика:
      - нет аутентифицированного пользователя -> 401
      - пользователь есть, но для его роли нет разрешающего правила -> 403
      - иначе доступ разрешён; при этом на view проставляется
        `request.access_scope = "own" | "all"`, чтобы во view/queryset можно
        было понять, показывать ли пользователю только свои объекты или все.
    """

    message = "У вас нет прав на выполнение этого действия."

    def has_permission(self, request, view):
        element_name = getattr(view, "business_element", None)
        if element_name is None:
            raise exceptions.APIException(
                "View не задал business_element для проверки прав доступа."
            )

        user = request.user
        if user is None or not getattr(user, "is_authenticated", False):
            raise exceptions.NotAuthenticated("Требуется аутентификация.")

        own_field, all_field = METHOD_TO_PERMISSION_FIELDS.get(
            request.method, (None, None)
        )
        if own_field is None:
            return False

        if user.role_id is None:
            return False

        try:
            rule = AccessRule.objects.get(role_id=user.role_id, element__name=element_name)
        except AccessRule.DoesNotExist:
            return False

        has_all = getattr(rule, all_field)
        has_own = getattr(rule, own_field)

        if has_all:
            request.access_scope = "all"
            return True
        if has_own:
            request.access_scope = "own"
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Если доступ разрешён только к "своим" объектам — проверяем владельца.
        scope = getattr(request, "access_scope", "own")
        if scope == "all":
            return True

        owner_id = getattr(obj, "owner_id", None)
        if owner_id is None:
            owner_id = getattr(obj, "owner", None)
        return owner_id == request.user.id
