from django.core.management.base import BaseCommand
from django.db import transaction

from access_control.models import AccessRule, BusinessElement
from users.models import Role, User

ROLE_NAMES = ["admin", "manager", "user", "guest"]

ELEMENTS = {
    "users": "Профили пользователей приложения",
    "roles": "Справочник ролей",
    "business_elements": "Справочник бизнес-объектов",
    "access_rules": "Правила доступа role<->element",
    "products": "Товары (демо-объект)",
    "stores": "Магазины (демо-объект)",
    "orders": "Заказы (демо-объект)",
}

FULL = dict(
    create_permission=True,
    read_permission=True, read_all_permission=True,
    update_permission=True, update_all_permission=True,
    delete_permission=True, delete_all_permission=True,
)
NONE = dict(
    create_permission=False,
    read_permission=False, read_all_permission=False,
    update_permission=False, update_all_permission=False,
    delete_permission=False, delete_all_permission=False,
)

# role -> element -> permissions dict (только не-NONE переопределения)
MATRIX = {
    "admin": {name: FULL for name in ELEMENTS},
    "manager": {
        "users": dict(NONE, read_permission=True, read_all_permission=True),
        "products": FULL,
        "stores": FULL,
        "orders": FULL,
    },
    "user": {
        "products": dict(
            NONE, create_permission=True,
            read_permission=True, read_all_permission=False,
            update_permission=True, delete_permission=True,
        ),
        "stores": dict(NONE, read_permission=True, read_all_permission=True),
        "orders": dict(
            NONE, create_permission=True,
            read_permission=True, read_all_permission=False,
            update_permission=True, delete_permission=True,
        ),
    },
    "guest": {
        "products": dict(NONE, read_all_permission=True),
        "stores": dict(NONE, read_all_permission=True),
    },
}

TEST_USERS = [
    {"email": "admin@example.com", "role": "admin", "first_name": "Анна", "last_name": "Админова"},
    {"email": "manager@example.com", "role": "manager", "first_name": "Максим", "last_name": "Менеджеров"},
    {"email": "user@example.com", "role": "user", "first_name": "Иван", "last_name": "Иванов"},
    {"email": "guest@example.com", "role": "guest", "first_name": "Гоша", "last_name": "Гостев"},
]
TEST_PASSWORD = "Password123!"


class Command(BaseCommand):
    help = "Наполняет БД ролями, бизнес-объектами, правилами доступа и тестовыми пользователями."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {}
        for name in ROLE_NAMES:
            role, _ = Role.objects.get_or_create(name=name)
            roles[name] = role
        self.stdout.write(self.style.SUCCESS(f"Роли готовы: {', '.join(roles)}"))

        elements = {}
        for name, description in ELEMENTS.items():
            element, _ = BusinessElement.objects.update_or_create(
                name=name, defaults={"description": description}
            )
            elements[name] = element
        self.stdout.write(self.style.SUCCESS(f"Бизнес-объекты готовы: {', '.join(elements)}"))

        rules_created = 0
        for role_name, element_map in MATRIX.items():
            for element_name, perms in element_map.items():
                AccessRule.objects.update_or_create(
                    role=roles[role_name],
                    element=elements[element_name],
                    defaults=perms,
                )
                rules_created += 1
        self.stdout.write(self.style.SUCCESS(f"Правил доступа создано/обновлено: {rules_created}"))

        for u in TEST_USERS:
            if User.objects.filter(email=u["email"]).exists():
                continue
            User.objects.create_user(
                email=u["email"],
                password=TEST_PASSWORD,
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=roles[u["role"]],
            )
        self.stdout.write(self.style.SUCCESS(
            f"Тестовые пользователи готовы (пароль для всех: {TEST_PASSWORD}):"
        ))
        for u in TEST_USERS:
            self.stdout.write(f"  - {u['email']} / роль: {u['role']}")
