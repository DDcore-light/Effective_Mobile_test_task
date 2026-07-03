import uuid

import bcrypt
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name


class UserManager(models.Manager):
    def create_user(self, email, password, first_name, last_name, patronymic="", role=None):
        if not email:
            raise ValueError("Email обязателен")
        if not password:
            raise ValueError("Пароль обязателен")

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_email(email):
        return email.strip().lower()


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    last_name = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    patronymic = models.CharField(max_length=150, blank=True, default="")

    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)

    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="users", null=True
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.email} ({self.role})"
    def set_password(self, raw_password: str) -> None:
        hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
        self.password_hash = hashed.decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(p for p in parts if p)
