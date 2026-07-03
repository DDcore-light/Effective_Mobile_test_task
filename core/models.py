from django.db import models


class TokenBlacklist(models.Model):
    """
    JWT — токен без состояния (stateless), поэтому чтобы logout реально
    "отзывал" токен до истечения его срока действия, идентификатор токена
    (jti) при logout записывается сюда и проверяется в JWTAuthentication.
    """
    jti = models.CharField(max_length=64, unique=True)
    user_id = models.UUIDField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "token_blacklist"
