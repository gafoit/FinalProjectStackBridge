# Финальный проект

Итог курса Python Backend: монолитное MVP «управление командой»

Проект написан на Django REST Framework. PostgreSQL запускается в Docker, само Django-приложение запускается локально.

## Стек

* Python 3.13
* Django 6.1
* Django REST Framework
* PostgreSQL 16
* Docker / Docker Compose
* django-filter
* pytest
* pytest-django
* pytest-cov

## Реализованный функционал

* Регистрация пользователей, с автоматическим созданием профиля для системы команды;
* Создание и управление командой, её участниками, задачами и встречами;
* Роли на уровне команды: `member`< `manager`< `admin`;
* Приглашение в команду по invite-коду;
* Передача владения командой;
* Задачи и назначение исполнителей;
* Статусы задач;
* Комментарии к задачам;
* Оценки выполненных задач;
* Средняя оценка конкретной задачи;
* Назначение встреч участников команды;
* Проверка занятости участников встреч при её планировании;
* Календарь с задачами и встречами текущего пользователя;
* Настроенная Admin-панель

---

## Запуск проекта

### Что понадобится

* Python 3.13
* Docker Desktop (Для контейнера PostgreSQL)
* Git

### 1. Скачать проект

```bash
git clone https://github.com/gafoit/FinalProjectStackBridge.git
cd FinalProjectStackBridge
```

### 2. Создать виртуальное окружение

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

Создать `.env` на основе `.env.example`.

Пример:

```env
POSTGRES_DB=final_project
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=change_me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

### 5. Запустить PostgreSQL

Или подключить свой

```bash
docker compose up -d
```

Проверить состояние контейнера:

```bash
docker compose ps
```

### 6. Применить миграции

```bash
python manage.py migrate
```

### 7. Создать администратора

```bash
python manage.py createsuperuser
```

### 8. Запустить Django

```bash
python manage.py runserver
```

После запуска:

```text
http://127.0.0.1:8000/
```

Админка:

```text
http://127.0.0.1:8000/admin/
```

---

# Тесты

Для тестов используется `pytest` и `pytest-django`.

Запустить все тесты:

```bash
pytest
```

Запустить тесты с coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

Проверить конфигурацию Django:

```bash
python manage.py check
```

Проект должен полностью проверяться с чистого клона после установки зависимостей и настройки PostgreSQL.

---

# API

Все API endpoints находятся под:

```text
/api/v1/
```

Для защищённых endpoints используется стандартная Django REST Framework session-аутентификация.

## Пользователи

### Регистрация

```http
POST /api/v1/users/
```

```json
{
    "user": {
        "username": "john",
        "email": "john@example.com",
        "password1": "password123",
        "password2": "password123"
    }
}
```

Профиль пользователя создаётся автоматически.

### Текущий пользователь

```http
GET /api/v1/users/me/
```

Пример ответа:

```json
{
    "username": "john",
    "email": "john@example.com"
}
```

Требуется авторизация.

### Смена пароля

```http
POST /api/v1/users/me/change_password/
```

```json
{
    "old_password": "old-password",
    "new_password1": "new-password",
    "new_password2": "new-password"
}
```

Старый пароль проверяется перед изменением.

---

# Команды

У команды есть владелец (owner) и участники с ролями:

* `member`
* `manager`
* `admin`

Владелец команды не является отдельной ролью membership, но имеет роль admin

### Создать команду

```http
POST /api/v1/teams/
```

```json
{
    "name": "Backend Team"
}
```

Создатель становится владельцем команды.

### Получить свои команды

```http
GET /api/v1/teams/
```

### Получить команду

```http
GET /api/v1/teams/{team_id}/
```

### Изменить команду

```http
PATCH /api/v1/teams/{team_id}/
```

```json
{
    "name": "New Team Name"
}
```

### Удалить команду

```http
DELETE /api/v1/teams/{team_id}/
```

Доступ зависит от роли пользователя.

### Присоединиться к команде

```http
POST /api/v1/teams/{team_id}/join/
```

```json
{
    "invite_code": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

После успешного присоединения пользователь добавляется в команду.

### Обновить invite-код

```http
POST /api/v1/teams/{team_id}/invite_code/
```

Создаёт новый invite-код команды. 

Сам код доступен ролям manager и выше, а изменение только admin

### Передать владение (Onwer)

```http
POST /api/v1/teams/{team_id}/transfer_ownership/
```

```json
{
    "profile": 12
}
```

Новый владелец должен уже состоять в команде. При успешной передаче даёт роль admin новому владельцу

---

# Участники команды

### Получить участников

```http
GET /api/v1/teams/{team_id}/members/
```

Пример:

```json
[
    {
        "profile": {
            "id": 1,
            "username": "john"
        },
        "role": "admin"
    },
    {
        "profile": {
            "id": 2,
            "username": "alice"
        },
        "role": "member"
    }
]
```

### Получить конкретного участника

```http
GET /api/v1/teams/{team_id}/members/{profile_id}/
```

### Изменить роль

```http
PATCH /api/v1/teams/{team_id}/members/{profile_id}/
```

```json
{
    "role": "manager"
}
```

Допустимые роли:

```text
member
manager
admin
```

Изменение роли ограничено иерархией прав.

### Удалить участника

```http
DELETE /api/v1/teams/{team_id}/members/{profile_id}/
```

---

# Задачи

Задача принадлежит команде и имеет один из трёх статусов:

```text
open
in_progress
done
```

Переходы:

```text
open         -> open / in_progress
in_progress  -> open / in_progress / done
done         -> done
```

После перехода в `done` вернуть задачу в предыдущий статус нельзя.

### Создать задачу

```http
POST /api/v1/teams/{team_id}/tasks/
```

```json
{
    "title": "Добавить авторизацию",
    "description": "Реализовать авторизацию пользователей",
    "assignee": 12,
    "due_date": "2026-09-20T18:00:00Z"
}
```

Исполнитель должен состоять в этой команде.

Создатель задачи определяется автоматически.

### Получить задачи команды

```http
GET /api/v1/teams/{team_id}/tasks/
```

### Получить задачу

```http
GET /api/v1/teams/{team_id}/tasks/{task_id}/
```

### Изменить задачу

```http
PATCH /api/v1/teams/{team_id}/tasks/{task_id}/
```

Например:

```json
{
    "status": "in_progress"
}
```

В зависимости от роли пользователь может изменять разные поля задачи.
Так, простой участник может только изменить статус, если он не создавал эту задачу.

### Получить задачи через общий endpoint

```http
GET /api/v1/tasks/
```

Доступны фильтры:

```text
?team=3
?assigned=me
?created=me
```

Например:

```text
/api/v1/tasks/?assigned=me
```

вернёт задачи, назначенные текущему пользователю.

---

# Комментарии

Комментарии находятся внутри задач.

### Получить комментарии

```http
GET /api/v1/tasks/{task_id}/comments/
```

### Добавить комментарий

```http
POST /api/v1/tasks/{task_id}/comments/
```

```json
{
    "text": "Задача готова к проверке."
}
```

Автор комментария определяется автоматически.

### Получить комментарий

```http
GET /api/v1/tasks/{task_id}/comments/{comment_id}/
```

### Изменить комментарий

```http
PATCH /api/v1/tasks/{task_id}/comments/{comment_id}/
```

```json
{
    "text": "Обновлённый текст комментария."
}
```

### Удалить комментарий

```http
DELETE /api/v1/tasks/{task_id}/comments/{comment_id}/
```

Изменять свой комментарий может его автор. Удаление также доступно пользователям с соответствующими правами в команде.

---

# Оценки задач

Оценить можно только выполненную задачу.

Один пользователь не может несколько раз оценить одну и ту же задачу.

### Добавить оценку

```http
POST /api/v1/tasks/{task_id}/evaluations/
```

```json
{
    "score": 5,
    "score_comment": "Отличная реализация."
}
```

Автор оценки определяется автоматически.

### Получить оценки задачи

```http
GET /api/v1/tasks/{task_id}/evaluations/
```

### Получить конкретную оценку

```http
GET /api/v1/tasks/{task_id}/evaluations/{evaluation_id}/
```

### Получить среднюю оценку

```http
GET /api/v1/tasks/{task_id}/evaluations/avg/
```

### Общий список оценок

```http
GET /api/v1/evaluations/
```

Доступны фильтры:

```text
?received=me
?created=me
```

---

# Встречи

Встреча относится к команде и содержит:

* название;
* описание;
* время начала;
* время окончания;
* организатора;
* участников;
* статус отмены.

Организатором автоматически становится текущий пользователь.

### Создать встречу

```http
POST /api/v1/teams/{team_id}/meetups/
```

```json
{
    "title": "Sprint Planning",
    "description": "Планирование следующего спринта",
    "starts_at": "2026-09-20T10:00:00Z",
    "ends_at": "2026-09-20T11:00:00Z",
    "participants": [12, 15]
}
```

Участники должны состоять в команде.

Организатор не добавляется автоматически в `participants`.

При создании проверяется:

* начало встречи раньше конца;
* отсутствие дублирующихся участников;
* участники состоят в команде;
* у организатора нет пересекающейся встречи;
* у участников нет пересекающихся встреч.

### Получить встречи команды

```http
GET /api/v1/teams/{team_id}/meetups/
```

### Получить встречу

```http
GET /api/v1/teams/{team_id}/meetups/{meetup_id}/
```

### Изменить встречу

```http
PATCH /api/v1/teams/{team_id}/meetups/{meetup_id}/
```

```json
{
    "title": "Обновлённая встреча",
    "starts_at": "2026-09-20T11:00:00Z",
    "ends_at": "2026-09-20T12:00:00Z",
    "participants": [12, 15]
}
```

Изменять и удалять встречу может только её организатор.

Отменённую встречу можно восстановить, но нельзя редактировать одновременно с восстановлением.

### Фильтры встреч

Общий endpoint:

```http
GET /api/v1/meetups/
```

Фильтр по команде:

```text
?team=3
```

Встречи, в которых текущий пользователь является участником:

```text
?participating=me
```

Встречи, которые текущий пользователь организует:

```text
?organizing=me
```

---

# Календарь

Календарь объединяет:

* задачи, назначенные текущему пользователю;
* встречи, где текущий пользователь является организатором или участником.

```http
GET /api/v1/calendar/
```

## Диапазон дат

Можно передать `from` и `to`.

### Без параметров

```http
GET /api/v1/calendar/
```

Возвращается текущая неделя: с понедельника 00:00 до начала следующего понедельника.

### Только `from`

```http
GET /api/v1/calendar/?from=2026-09-14T00:00:00Z
```

Если `to` не указан, используется текущее время.

### Только `to`

```http
GET /api/v1/calendar/?to=2026-09-20T00:00:00Z
```

Если `from` не указан, используется текущее время.

### Оба параметра

```http
GET /api/v1/calendar/?from=2026-09-14T00:00:00Z&to=2026-09-21T00:00:00Z
```

`from` не может быть позже `to`.

Пример задачи в календаре:

```json
{
    "type": "task",
    "id": 10,
    "title": "Добавить авторизацию",
    "due_date": "2026-09-18T18:00:00Z",
    "status": "in_progress",
    "team": {
        "id": 3,
        "name": "Backend Team"
    }
}
```

Пример встречи:

```json
{
    "type": "meetup",
    "id": 7,
    "title": "Sprint Planning",
    "starts_at": "2026-09-18T10:00:00Z",
    "ends_at": "2026-09-18T11:00:00Z",
    "is_cancelled": false,
    "team": {
        "id": 3,
        "name": "Backend Team"
    }
}
```

События возвращаются в хронологическом порядке.

---

# Фильтрация и пагинация

Для API включены стандартные механизмы DRF:

* filtering;
* search;
* ordering;
* pagination.

Размер страницы по умолчанию:

```text
10
```

---

# Docker

В Docker запускается только PostgreSQL. Django работает непосредственно на хостовой машине.

Запустить PostgreSQL:

```bash
docker compose up -d
```

Остановить:

```bash
docker compose down
```

Удалить контейнер вместе с volume базы:

```bash
docker compose down -v
```

---

# Полезные команды

Создать миграции:

```bash
python manage.py makemigrations
```

Применить миграции:

```bash
python manage.py migrate
```

Создать администратора:

```bash
python manage.py createsuperuser
```

Запустить сервер:

```bash
python manage.py runserver
```

Проверить Django:

```bash
python manage.py check
```

Запустить тесты:

```bash
pytest
```

Запустить тесты с coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

---

## Структура проекта

```text
FinalProjectStackBridge/
├── FinalProject/       # настройки Django и URL проекта
├── profiles/           # пользователи и профили
├── teams/              # команды и участники
├── tasks/              # задачи, комментарии и оценки
├── meetups/            # встречи
├── ya_calendar/        # календарь
├── manage.py
├── pytest.ini
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

## Переменные окружения

| Переменная             | Назначение              |
| ---------------------- | ----------------------- |
| `POSTGRES_DB`          | Имя базы PostgreSQL     |
| `POSTGRES_USER`        | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD`    | Пароль PostgreSQL       |
| `POSTGRES_HOST`        | Хост PostgreSQL         |
| `POSTGRES_PORT`        | Порт PostgreSQL         |
| `DJANGO_SECRET_KEY`    | Секретный ключ Django   |
| `DJANGO_DEBUG`         | Режим отладки           |
| `DJANGO_ALLOWED_HOSTS` | Разрешённые hosts       |

Реальный `.env` с паролями и секретным ключом в репозиторий добавлять не нужно. Для настройки используется `.env.example`.

---
