# Expedition Service

Backend service for managing expeditions with real-time WebSocket events.

## Tech Stack

- **Django 4.2** + Django REST Framework
- **Django Channels** + Daphne (WebSocket support)
- **PostgreSQL** (production) / SQLite (development)
- **Redis** (channel layer for WebSocket broadcasting)
- **JWT** authentication via djangorestframework-simplejwt

## Running Locally

**Requirements:** Python 3.11, pip

```bash
# create and activate virtual environment
python -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# run migrations
python manage.py migrate

# start server
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

The server will be available at `http://localhost:8000`.

## Running with Docker

**Requirements:** Docker, Docker Compose

```bash
docker compose up --build
```

This starts three services: the Django app, PostgreSQL, and Redis.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | insecure dev key |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL | SQLite |
| `REDIS_URL` | Redis URL | in-memory channel layer |

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain JWT token pair |
| `POST` | `/api/token/refresh/` | Refresh access token |

### Users

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/users/` | Register user | No |
| `GET` | `/api/users/me/` | Current user profile | Yes |

### Expeditions

| Method | Endpoint | Description | Role |
|---|---|---|---|
| `GET` | `/api/expeditions/` | List own expeditions | Any |
| `POST` | `/api/expeditions/` | Create expedition | Chief |
| `GET` | `/api/expeditions/{id}/` | Get expedition | Member/Chief |
| `POST` | `/api/expeditions/{id}/status/` | Change status | Chief |
| `POST` | `/api/expeditions/{id}/invite/` | Invite member | Chief |
| `POST` | `/api/expeditions/{id}/confirm/` | Confirm participation | Invited member |
| `GET` | `/api/expeditions/{id}/members/` | List members | Member/Chief |

## Example Requests

**Register a user:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "chief@example.com", "name": "John", "password": "pass123", "role": "chief"}'
```

**Get token:**
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "chief@example.com", "password": "pass123"}'
```

**Create expedition:**
```bash
curl -X POST http://localhost:8000/api/expeditions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"title": "Arctic Expedition", "start_at": "2026-05-01T08:00:00Z", "capacity": 5}'
```

**Invite member:**
```bash
curl -X POST http://localhost:8000/api/expeditions/{id}/invite/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"user_id": 2}'
```

## Expedition Status Flow

```
draft → ready → active → finished
```

| Transition | Who | Conditions |
|---|---|---|
| `draft → ready` | Chief | — |
| `ready → active` | Chief | `start_at <= now`, min 2 confirmed members, confirmed <= capacity, no member in another active expedition |
| `active → finished` | Chief | — |

## WebSocket

Connect to receive real-time expedition events:

```bash
wscat -c "ws://localhost:8000/ws/expeditions/?token=<access_token>"
```

On connect, the client is automatically subscribed to all expeditions it belongs to (as chief or member). New invitations are handled automatically — no manual subscribe needed.

### Events

| Event | Trigger |
|---|---|
| `member_invited` | A member is invited to an expedition |
| `member_confirmed` | A member confirms participation |
| `expedition_status` | Expedition status changes |

### Client Actions

```json
{"action": "subscribe", "expedition_id": 1}
{"action": "unsubscribe", "expedition_id": 1}
{"action": "ping"}
```

## Running Tests

```bash
pytest tests/ -v
```
