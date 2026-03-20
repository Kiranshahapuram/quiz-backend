# Quiz Backend

A REST API for generating AI-powered quizzes, managing communities, tracking quiz attempts, and analysing user performance. Built with Django and Django REST Framework, backed by PostgreSQL and Redis.

**Repository:** https://github.com/Kiranshahapuram/quiz-backend

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Local Setup](#local-setup)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Design Decisions and Trade-offs](#design-decisions-and-trade-offs)
6. [AI Integration](#ai-integration)
7. [Challenges and Solutions](#challenges-and-solutions)
8. [Testing](#testing)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5, Django REST Framework |
| Database | PostgreSQL |
| Cache & Broker | Redis via django-redis |
| Background tasks | Celery |
| Auth | JWT via djangorestframework-simplejwt |
| AI providers | Groq (llama-3.3-70b) or Google Gemini 2.0 Flash |
| Server | Daphne (ASGI) |
| Deployment | Railway |

---

## Local Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (or use the SQLite fallback for local dev)
- Redis

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/Kiranshahapuram/quiz-backend.git
cd quiz-backend
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/quiz_db
REDIS_URL=redis://localhost:6379/1
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
CELERY_TASK_ALWAYS_EAGER=false
```

If neither AI key is provided, the service falls back to a mock question generator so the rest of the application still runs.

Get a free Groq API key at https://console.groq.com  
Get a free Gemini API key at https://aistudio.google.com/app/apikey

**5. Create the database**

```bash
psql -U postgres -c "CREATE DATABASE quiz_db;"
```

**6. Run migrations**

```bash
python manage.py migrate
```

**7. Create a superuser (admin role)**

```bash
python manage.py createsuperuser
```

After creating the superuser, set their role to `admin` via the Django admin panel at `/admin/` or directly in the shell:

```bash
python manage.py shell
>>> from apps.users.models import User
>>> u = User.objects.get(email='your@email.com')
>>> u.role = 'admin'
>>> u.save()
```

**8. Start the development server**

In one terminal:

```bash
python manage.py runserver
```

In a second terminal (required for quiz generation):

```bash
celery -A config worker --loglevel=info
```

The API is now running at `http://localhost:8000/api/v1/`

---

## Database Schema

### Models and relationships

```
User
 |-- QuizRequest (many)        A user can submit multiple generation requests
 |-- Attempt (many)            A user can attempt multiple quizzes
 |-- Community (many, creator) A user can create multiple communities
 |-- Community (many, member)  A user can be a member of multiple communities

Community
 |-- QuizRequest (many)        Quizzes can be scoped to a community
 |-- Quiz (many)               Published quizzes belong to a community or are personal

QuizRequest
 |-- Quiz (one, nullable)      Produces one Quiz on success, null on failure or pending

Quiz
 |-- Question (many)           A quiz contains multiple questions
 |-- QuizAnalytics (one)       Pre-computed aggregate statistics

Question
 |-- Option (many)             Each question has multiple answer options

Attempt
 |-- AttemptAnswer (many)      One answer record per question
```

### Model summary

| Model | Key Fields | Key Constraints |
|---|---|---|
| User | email, username, role, is_active | email unique, role in (user, admin) |
| Community | name, description, join_code, creator, members | join_code unique, auto-generated on create |
| QuizRequest | user, topic, difficulty, question_count, status, community | status in (pending, processing, completed, failed), question_count 1-50 |
| Quiz | title, topic, difficulty, time_limit_secs, is_published, community, deleted_at | quiz_request OneToOne |
| Question | body, order, points | points default 10 |
| Option | body, is_correct, order | one is_correct=True per question (partial unique constraint) |
| Attempt | user, quiz, status, score, max_score, started_at, submitted_at | unique_together (user, quiz) |
| AttemptAnswer | attempt, question, selected_option, is_correct, points_awarded | is_correct and points_awarded written at scoring time |
| QuizAnalytics | quiz, total_attempts, avg_score_pct, avg_completion_secs, question_stats | quiz OneToOne |

### Notes on key design choices

`QuizRequest` and `Quiz` are separate models. A request tracks intent and generation status; a quiz record is only created on successful generation. A failed or in-progress request never produces a partial quiz.

`Attempt.unique_together = (user, quiz)` is enforced at the database level, not just in application logic. This prevents duplicate attempts even under concurrent requests.

`AttemptAnswer.is_correct` and `points_awarded` are written once at submission time and never re-derived. Skipped questions receive a ghost `AttemptAnswer` record with `is_correct=False` and `points_awarded=0`, ensuring the result breakdown is always complete.

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`. All endpoints except register and login require a `Bearer` token in the `Authorization` header.

### Error response format

Every error follows this consistent shape:

```json
{
  "code": "MACHINE_READABLE_CODE",
  "message": "Human readable description",
  "field": "field_name",
  "details": {}
}
```

`field` and `details` are only present on validation errors.

---

### Authentication  —  `/api/v1/auth/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register/` | Create a new user account. Returns user object and token pair. | None |
| POST | `/auth/login/` | Authenticate with email and password. Returns user object and token pair. | None |
| POST | `/auth/refresh/` | Exchange a refresh token for a new access token. | None |
| POST | `/auth/logout/` | Blacklist the refresh token. Returns 204. | JWT |

Token lifetimes: access token 30 minutes, refresh token 7 days.

---

### Communities  —  `/api/v1/communities/`

Communities allow groups of users to share quizzes. Each community has a unique join code that other users can use to join.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/communities/` | List communities the current user is a member of. | JWT |
| POST | `/communities/` | Create a new community. The creator is automatically added as a member. | JWT |
| GET | `/communities/{id}/` | Retrieve a specific community. | JWT |
| PUT / PATCH | `/communities/{id}/` | Update community details. | JWT |
| DELETE | `/communities/{id}/` | Delete a community. | JWT |
| POST | `/communities/join/` | Join a community using its join code. Body: `{ "join_code": "ABC123" }` | JWT |

---

### Quiz generation  —  `/api/v1/quizzes/quiz-requests/`

Quiz generation is asynchronous. The create endpoint returns immediately and the client polls for status.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/quizzes/quiz-requests/` | Submit a generation request. Returns 202 with status `pending`. Optionally pass `community` UUID to scope the quiz to a community. | JWT |
| GET | `/quizzes/quiz-requests/` | List the current user's generation requests. Cursor paginated. | JWT |
| GET | `/quizzes/quiz-requests/{id}/` | Get a single request. Poll this until `status` is `completed` — `quiz_id` is populated on success. | JWT |

**Generation status values:** `pending` → `processing` → `completed` or `failed`

**Request body for POST:**
```json
{
  "topic": "Python decorators",
  "difficulty": "medium",
  "question_count": 5,
  "community": "uuid-of-community-or-omit-for-personal"
}
```

---

### Quizzes  —  `/api/v1/quizzes/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/quizzes/` | List published quizzes accessible to the current user. Filterable by `topic`, `difficulty`, and `community` (pass `personal` to filter personal quizzes). Cursor paginated. | JWT |
| GET | `/quizzes/{id}/` | Quiz detail with all questions and options. Correct answers are never exposed here. Cached for 1 hour. | JWT |
| GET | `/quizzes/{id}/analytics/` | Pre-computed analytics for the quiz. Accessible to the quiz creator, community members, and admins. Cached for 15 minutes. | JWT |

**Quiz visibility rules:**
- Community quizzes are visible to members of that community.
- Personal quizzes (no community) are visible only to the user who created them.

---

### Attempts  —  `/api/v1/attempts/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/attempts/` | Start an attempt. Body: `{ "quiz_id": "uuid" }`. Returns 201. | JWT |
| GET | `/attempts/{id}/` | View attempt state. Correct answers are omitted while status is `in_progress`. | JWT (owner) |
| PATCH | `/attempts/{id}/answer/` | Save or update an answer. Body: `{ "question_id": "uuid", "option_id": "uuid" }`. Can be called multiple times — last write wins. | JWT (owner) |
| POST | `/attempts/{id}/submit/` | Lock and score the attempt. Returns full result with correct answers revealed. Triggers analytics update. | JWT (owner) |

**Attempt status values:** `in_progress` → `submitted`

Skipped questions are recorded as incorrect automatically on submission.

---

### User  —  `/api/v1/users/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/users/me/history/` | Paginated attempt history for the current user. Cursor paginated by `submitted_at` descending. | JWT |
| GET | `/users/me/performance/` | Aggregated performance stats: overall average, breakdown by topic and difficulty, best and weakest topics. Cached for 5 minutes. | JWT |

---

### Admin  —  `/api/v1/admin/`

These endpoints require a user with `role = admin`.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/admin/quizzes/` | List all quizzes including unpublished. | Admin JWT |
| GET | `/admin/quizzes/{id}/` | Retrieve any quiz. | Admin JWT |
| PUT / PATCH | `/admin/quizzes/{id}/` | Edit a quiz. Invalidates the quiz detail cache on save. | Admin JWT |
| DELETE | `/admin/quizzes/{id}/` | Soft delete — sets `deleted_at` and `is_published=False`. Returns 204. | Admin JWT |

---

## Design Decisions and Trade-offs

### Separating QuizRequest from Quiz

Quiz generation calls an external AI API that can fail, time out, or require retrying. If the request and the resulting quiz were the same record, any mid-generation failure would leave a broken or partially-populated quiz in the database.

Keeping them separate means `QuizRequest` tracks intent and generation status independently. A `Quiz` record is only created inside a database transaction on successful generation. The trade-off is a slightly more complex generation flow and a polling pattern on the client side, both of which are worthwhile given the data integrity benefit.

### Asynchronous generation with Celery

The generation endpoint returns `202 Accepted` immediately and dispatches work to a Celery background task. The client polls `GET /quizzes/quiz-requests/{id}/` until the status is `completed`.

The synchronous alternative — blocking the HTTP request for the duration of the AI call — would hold the connection open for 5 to 15 seconds, cause timeouts on Railway's infrastructure, and provide no feedback to the user during generation. The async approach is the correct choice for any endpoint that depends on an external service.

### Dual AI provider support

The `AIService` supports both Groq and Gemini. At startup it checks which API key is configured and routes to that provider. If neither key is present, it falls back to a mock generator so the rest of the application remains testable without external credentials. This makes local development significantly easier without any conditional logic scattered across the codebase.

### Community-scoped quizzes

Quizzes can be either personal (visible only to the creator) or scoped to a community (visible to all community members). This is implemented through an optional `community` foreign key on both `QuizRequest` and `Quiz`. Community membership is checked at the quiz request creation step, the quiz list step, and the attempt creation step, ensuring that access control is enforced at every entry point.

### Denormalized scoring

When an attempt is submitted, `is_correct` and `points_awarded` are written directly onto each `AttemptAnswer` row and never re-derived. Skipped questions receive a ghost answer record with both fields set to false and zero respectively.

The alternative is to join `Option.is_correct` at read time. The problem is that quiz options could be edited after an attempt has already been scored, which would silently change historical results. Locking correctness at submission time creates an audit-safe, immutable record.

### Pre-computed analytics

`QuizAnalytics` is updated by a Celery task that fires after each attempt submission. The analytics endpoint reads from this pre-computed row and never aggregates inline. Running aggregation queries across potentially thousands of attempt records on every GET request would produce unpredictable latency under load.

### Cursor-based pagination

All list endpoints use cursor pagination via `CustomCursorPagination`. Offset queries such as `LIMIT 10 OFFSET 5000` require the database to scan and discard thousands of rows before returning the requested page. Cursor pagination uses an indexed column as the reference point and maintains consistent performance regardless of dataset size.

---

## AI Integration

Quiz questions are generated using either the Groq API (llama-3.3-70b-versatile) or the Google Gemini 2.0 Flash API, selected automatically based on which API key is configured. Both are free tier services.

### Provider selection

```
GROQ_API_KEY set and valid  →  use Groq
GEMINI_API_KEY set and valid  →  use Gemini
Neither key present  →  use mock generator
```

### Generation flow

1. User submits `POST /quizzes/quiz-requests/` with topic, difficulty, and question count.
2. A `QuizRequest` record is created with `status=pending` and `202 Accepted` is returned immediately.
3. A Celery task picks up the request, sets `status=processing`, and calls `AIService.generate_questions()`.
4. The service sends a structured prompt requesting JSON-only output with a defined schema.
5. The response is parsed, markdown fences are stripped if present, and the structure is validated — exactly one `is_correct: true` per question is required.
6. On success, `QuizService.create_quiz_from_questions()` creates the Quiz, Questions, and Options in a single atomic transaction.
7. `QuizRequest.status` is set to `completed` and `quiz_id` is populated.
8. On `AIRateLimitError`, the task resets status to `pending` and retries after a 120-second delay.
9. On any other failure, the task retries automatically up to 3 times with exponential backoff. After 3 failures, `status=failed` and `failure_reason` is recorded.

### Prompt structure

Both providers receive the same prompt requesting raw JSON output with no markdown or explanation:

```
Generate a quiz about '{topic}' with difficulty '{difficulty}'.
I need exactly {count} multiple choice questions.
For each question, provide 4 options where EXACTLY ONE is correct.

Output MUST be pure JSON matching this exact schema:
{
    "questions": [
        {
            "body": "Question text here",
            "options": [
                {"body": "Option text here", "is_correct": true},
                {"body": "Wrong option", "is_correct": false},
                ...
            ],
            "explanation": "Explanation for the correct answer"
        }
    ]
}
Output ONLY the raw JSON object.
```

### Time limit

Each generated quiz receives an automatic time limit of one minute per question (e.g. a 10-question quiz gets a 600-second limit), set in `QuizService.create_quiz_from_questions()`.

---

## Challenges and Solutions

### AI response inconsistency

Both AI providers occasionally return JSON wrapped in markdown code fences despite being instructed not to. The `_parse_and_validate` method in `AIService` strips these fences before parsing, and raises `AIServiceError` if the resulting JSON does not match the expected structure. Combined with the Celery retry mechanism, this handles the majority of transient formatting issues without manual intervention.

### Preventing correct answer leakage

The quiz detail endpoint must never reveal which option is correct. This is enforced by using a separate `PublicOptionSerializer` that explicitly excludes the `is_correct` field — not just by omitting it from a shared serializer. On the attempt side, `AttemptResultSerializer` checks `attempt.status` before deciding what to include: in-progress attempts receive only `question_id`, `selected_option_id`, and `answered_at`; completed attempts receive the full breakdown including correct answers.

### Celery task idempotency

The generation task checks `quiz_request.status != 'pending'` at the start before doing any work. If the task is retried after partially completing — for example, after the quiz was created but before the status was updated — the check prevents a second quiz from being created, since the status will already be `processing` or `completed`.

### Community access control at multiple layers

Quiz visibility is not a single permission check. It is enforced at the queryset level in `QuizViewSet.get_queryset()`, at the attempt creation step in `AttemptViewSet.create()`, and at the quiz request creation step in `QuizRequestCreateSerializer.validate_community()`. This ensures that a user who is removed from a community cannot access its quizzes through any entry point.

---

## Testing

Manual testing was performed after each development phase using Postman, with defined inputs and expected outputs for each scenario.

Scenarios covered:

- Full generation flow: submit request, poll until `completed`, verify quiz detail response contains no `is_correct` field on any option
- Community quiz flow: create community, generate community quiz, verify non-member cannot see or attempt it
- Full attempt flow: start, answer all questions, submit, verify `score` equals the sum of `points_awarded` across all answers
- Skipped questions: submit with unanswered questions, verify those score zero and correct answers are revealed in the result
- Duplicate attempt: attempting the same quiz twice returns `409 DUPLICATE_ATTEMPT`
- Permission enforcement: accessing another user's attempt returns `403 PERMISSION_DENIED`
- Soft delete: a deleted quiz returns `404` on the public endpoint but the record remains in the database with `deleted_at` set
- Admin access: admin endpoints return `403` when called with a non-admin token

Automated test coverage is not included in this version. A follow-up pass would add unit tests for `AttemptService.score_attempt()`, `AIService._parse_and_validate()`, and integration tests covering the full generation and attempt flows across both personal and community quiz types.
