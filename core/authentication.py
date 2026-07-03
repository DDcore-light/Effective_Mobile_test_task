import jwt
from django.utils import timezone
from rest_framework import authentication, exceptions

from core.models import TokenBlacklist
from users.models import User


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Собственная (не basic/session/simplejwt "из коробки") реализация
    аутентификации по заголовку:

        Authorization: Bearer <token>

    Поведение соответствует ТЗ:
      - нет заголовка / некорректный или просроченный токен / пользователь
        не найден / пользователь деактивирован  -> None (анонимный запрос,
        далее permission-класс сам вернёт 401, если ресурс требует логина);
      - валидный токен -> request.user = User instance, request.auth = payload.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header or not header.startswith(f"{self.keyword} "):
            return None

        token = header[len(self.keyword) + 1:].strip()
        if not token:
            return None

        try:
            from core.utils.jwt_utils import decode_token
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Токен истёк")
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("Невалидный токен")

        jti = payload.get("jti")
        if jti and TokenBlacklist.objects.filter(jti=jti).exists():
            raise exceptions.AuthenticationFailed("Токен отозван (logout)")

        try:
            user = User.objects.select_related("role").get(id=payload["sub"])
        except (User.DoesNotExist, ValueError, KeyError):
            raise exceptions.AuthenticationFailed("Пользователь не найден")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("Аккаунт деактивирован")

        return (user, payload)

    def authenticate_header(self, request):
        # Наличие этого метода заставляет DRF возвращать 401 (а не 403)
        # для запросов без валидной аутентификации.
        return self.keyword
