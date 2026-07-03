import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


def generate_access_token(user) -> tuple[str, str, datetime]:
    """
    Генерирует JWT для пользователя. Возвращает (token, jti, expires_at).
    Токен несёт id пользователя и роль — этого достаточно, чтобы
    JWTAuthentication подняла пользователя из БД и проверила его is_active
    (роль в токене используется только как подсказка/кэш, реальная роль
    всегда перечитывается из БД при проверке прав).
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.JWT_ACCESS_TTL_SECONDS)
    jti = uuid.uuid4().hex

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.name if user.role_id else None,
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str) -> dict:
    """Бросает jwt.PyJWTError при невалидном/просроченном токене."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
