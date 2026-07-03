# Backend: собственная система аутентификации и авторизации

Учебный проект по ТЗ: backend-приложение (Django + Django REST Framework +
PostgreSQL) с **собственной** системой аутентификации (JWT + bcrypt,
без `djangorestframework-simplejwt` и без `django.contrib.auth`) и
**собственной** ролевой системой авторизации на уровне отдельных
бизнес-объектов (RBAC с разграничением "свои" / "все" объекты).

## Стек

- Python 3.12, Django 6, Django REST Framework
- PostgreSQL (рекомендовано ТЗ), опционально SQLite для быстрого запуска
- `PyJWT` — генерация/проверка JWT
- `bcrypt` — хеширование паролей

## Быстрый старт

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # поправьте значения при необходимости

# для быстрого запуска без Postgres:
# в .env выставьте DB_ENGINE=sqlite

python manage.py migrate
python manage.py seed_data   # создаст роли, права и тестовых пользователей
python manage.py runserver
```

После `seed_data` доступны тестовые пользователи (пароль у всех
`Password123!`):

| email                 | роль    |
|-----------------------|---------|
| admin@example.com     | admin   |
| manager@example.com   | manager |
| user@example.com      | user    |
| guest@example.com     | guest   |

## 1. Модуль "Взаимодействие с пользователем"

Собственная модель `users.User` (НЕ наследует `AbstractUser`/`PermissionsMixin`
из `django.contrib.auth` — вся логика реализована вручную).

Пароль хранится как bcrypt-хеш (`User.set_password` / `check_password`,
библиотека `bcrypt`), в БД никогда не попадает открытый текст.

| Метод | Путь                     | Действие |
|-------|--------------------------|----------|
| POST  | `/api/auth/register/`    | Регистрация: фамилия, имя, отчество, email, пароль, повтор пароля |
| POST  | `/api/auth/login/`       | Вход по email + паролю → выдаётся JWT |
| POST  | `/api/auth/logout/`      | Выход: текущий токен заносится в blacklist |
| GET   | `/api/auth/me/`          | Данные текущего пользователя |
| PATCH | `/api/auth/me/`          | Обновление профиля (ФИО) |
| DELETE| `/api/auth/me/`          | Мягкое удаление: `is_active=False` + logout. Запись в БД остаётся, повторный логин после этого возвращает 401 "Аккаунт деактивирован" |

### Идентификация пользователя после login

Реализована **не через `django.contrib.auth`**, а через собственный класс
`core.authentication.JWTAuthentication` (DRF `BaseAuthentication`):

1. Клиент присылает заголовок `Authorization: Bearer <token>`.
2. Токен (HS256, библиотека `PyJWT`) декодируется, проверяется срок
   действия и наличие `jti` в таблице `token_blacklist` (запись туда
   добавляется при logout / мягком удалении — так реализован реальный
   отзыв доступа для, по сути, stateless JWT).
3. Пользователь поднимается из БД по `sub` (id), проверяется `is_active`.
4. Пользователь кладётся в `request.user`, полезная нагрузка токена — в
   `request.auth`. Все последующие вьюхи в рамках запроса используют
   `request.user`.

Альтернативный вариант (не реализован, но заложен в ТЗ) — сессии:
таблица `sessions`, cookie `sessionid` + `expires_at`, `request.user`
проставляется в кастомном middleware. Архитектурно заменить JWT на
сессии можно, поменяв только `core/authentication.py`.

## 2. Система разграничения прав доступа

### Схема БД

```
roles                    business_elements            access_roles_rules
--------------------     --------------------------    -------------------------------
id                        id                            id
name (admin/manager/...)  name (users/products/...)     role_id     -> roles.id
description                description                  element_id  -> business_elements.id
                                                          create_permission        bool
                                                          read_permission           bool  (свои)
                                                          read_all_permission       bool  (все)
                                                          update_permission         bool  (свои)
                                                          update_all_permission     bool  (все)
                                                          delete_permission         bool  (свои)
                                                          delete_all_permission     bool  (все)
```

- **roles** — справочник ролей (`admin`, `manager`, `user`, `guest` — заведены
  сидом, можно добавлять новые через API).
- **business_elements** — справочник объектов приложения, к которым
  регулируется доступ (`users`, `roles`, `business_elements`, `access_rules`,
  `products`, `stores`, `orders`).
- **access_roles_rules** — правило "роль X имеет право Y на элемент Z".
  Для каждого действия есть пара полей `..._permission` /
  `..._all_permission`: первое разрешает работу только со **своими**
  объектами (`owner == текущий пользователь`), второе — со **всеми**
  объектами данного типа. `create_permission` не различает own/all,
  так как у ещё не созданного объекта владельца нет.

Модели: `users/models.py` (`Role`, `User`), `access_control/models.py`
(`BusinessElement`, `AccessRule`).

### Как это работает на уровне запроса

`core/permissions.py` → `ResourcePermission` (DRF `BasePermission`),
применяется ко всем защищённым бизнес-вьюхам. Каждая вьюха объявляет,
к какому элементу она относится:

```python
class ProductListView(APIView):
    business_element = "products"
    permission_classes = [ResourcePermission]
```

Логика `has_permission`:

1. Нет `request.user` (не прошла аутентификация) → **401** `NotAuthenticated`.
2. Пользователь есть, но для его роли нет правила на данный
   `business_element`, либо оба флага (own/all) выключены для
   текущего HTTP-метода → **403** `PermissionDenied`.
3. Иначе доступ разрешён; `request.access_scope` выставляется в
   `"own"` или `"all"` — вьюха использует это, чтобы отфильтровать
   выдаваемые объекты (только свои либо вообще все).

Сопоставление HTTP-метода и колонки правила:

| HTTP   | own-поле            | all-поле                |
|--------|----------------------|--------------------------|
| GET    | read_permission       | read_all_permission      |
| POST   | create_permission      | create_permission (общее)|
| PUT/PATCH | update_permission  | update_all_permission    |
| DELETE | delete_permission      | delete_all_permission    |

### Администрирование правил (для роли admin)

| Метод | Путь                                   | Действие |
|-------|-----------------------------------------|----------|
| GET/POST | `/api/access-control/roles/`         | Список / создание ролей |
| GET/POST | `/api/access-control/elements/`      | Список / создание бизнес-объектов |
| GET/POST | `/api/access-control/rules/`         | Список / создание правил доступа |
| GET/PATCH/DELETE | `/api/access-control/rules/<id>/` | Просмотр / изменение / удаление конкретного правила |

Эти эндпоинты сами защищены той же системой (`business_element =
"roles" / "business_elements" / "access_rules"`) — по сидовым данным
полный доступ к ним есть только у роли `admin`.

## 3. Демонстрационные бизнес-объекты (Mock)

Согласно ТЗ таблицы в БД для них не создаются — это in-memory
Mock-данные (`business/data.py`: `PRODUCTS`, `STORES`, `ORDERS`), к
которым применяется та же ролевая система прав, что и к реальным
ресурсам:

| Метод | Путь                              |
|-------|------------------------------------|
| GET/POST | `/api/business/products/`       |
| GET/PATCH/DELETE | `/api/business/products/<id>/` |
| GET/POST | `/api/business/stores/`         |
| GET/PATCH/DELETE | `/api/business/stores/<id>/` |
| GET/POST | `/api/business/orders/`         |
| GET/PATCH/DELETE | `/api/business/orders/<id>/` |

Список отдаёт только "свои" объекты (`owner == email текущего
пользователя`), если у роли нет `..._all_permission`, иначе — все.

## Коды ошибок

- **401 Unauthorized** — не удалось определить пользователя по
  запросу (нет токена / просрочен / отозван (после logout) / нет
  такого пользователя / пользователь деактивирован).
- **403 Forbidden** — пользователь определён, но по правилам роли ему
  не разрешено выполнять запрошенное действие над данным
  business_element (или конкретным чужим объектом).

## Матрица прав, создаваемая `seed_data`

| Роль | users | products / stores / orders | roles / business_elements / access_rules |
|------|-------|------------------------------|--------------------------------------------|
| admin | всё | всё | всё |
| manager | read (все) | всё (все объекты) | нет доступа |
| user | — | products/orders: свои (CRUD); stores: read (все) | нет доступа |
| guest | — | products/stores: read (все), без записи | нет доступа |

## Проверка вручную (curl)

```bash
# логин
curl -X POST localhost:8000/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123!"}'

# запрос без токена -> 401
curl localhost:8000/api/business/products/

# запрос с токеном обычного пользователя к админскому ресурсу -> 403
curl localhost:8000/api/access-control/rules/ -H "Authorization: Bearer <token>"
```

## Структура проекта

```
config/            # settings, urls
core/               # JWT-аутентификация, permission-класс, blacklist, exception handler
users/               # модель User/Role, регистрация/логин/логаут/профиль, seed_data
access_control/      # BusinessElement, AccessRule + admin API
business/            # mock-объекты products/stores/orders
```
