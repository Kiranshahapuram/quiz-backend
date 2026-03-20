# API Documentation

**Base URL:** `https://your-app.up.railway.app/api/v1`  
**Content-Type:** `application/json` for all requests  
**Authentication:** `Authorization: Bearer <access_token>` for all protected endpoints

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Communities](#2-communities)
3. [Quiz Requests](#3-quiz-requests)
4. [Quizzes](#4-quizzes)
5. [Attempts](#5-attempts)
6. [User](#6-user)
7. [Admin](#7-admin)
8. [Error Reference](#8-error-reference)
9. [Pagination](#9-pagination)

---

## Conventions

### Request headers

| Header | Value | When |
|---|---|---|
| `Content-Type` | `application/json` | All POST, PUT, PATCH requests |
| `Authorization` | `Bearer <access_token>` | All protected endpoints |

### Response envelope — errors

Every error response, regardless of source, follows this exact shape:

```json
{
  "code": "MACHINE_READABLE_CODE",
  "message": "Human readable description",
  "field": "field_name",
  "details": {
    "field_name": ["Error message."]
  }
}
```

`field` and `details` are only present on `VALIDATION_ERROR` responses.

### Timestamps

All timestamps are ISO 8601 UTC strings. Example: `"2025-03-19T10:30:00Z"`

### IDs

All IDs are UUID v4 strings. Example: `"9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"`

---

## 1. Authentication

### 1.1 Register

**`POST /auth/register/`** — No auth required

Creates a new user account and returns a JWT token pair.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | Yes | Must be unique. |
| `username` | string | Yes | Display name. |
| `password` | string | Yes | Must contain at least one letter and one number. Django's default validators also apply. |

```json
{
  "email": "ada@example.com",
  "username": "ada_codes",
  "password": "Secret123"
}
```

**Response — 201 Created**

```json
{
  "user": {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "email": "ada@example.com",
    "username": "ada_codes",
    "role": "user",
    "is_active": true
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Missing fields, invalid email, weak password. Check `details` for field-level messages. |

---

### 1.2 Login

**`POST /auth/login/`** — No auth required

Authenticates with email and password. Returns a JWT token pair and user object.

**Request body**

| Field | Type | Required |
|---|---|---|
| `email` | string | Yes |
| `password` | string | Yes |

```json
{
  "email": "ada@example.com",
  "password": "Secret123"
}
```

**Response — 200 OK**

```json
{
  "user": {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "email": "ada@example.com",
    "username": "ada_codes",
    "role": "user",
    "is_active": true
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Email not found or password incorrect. |

---

### 1.3 Refresh token

**`POST /auth/refresh/`** — No auth required

Exchanges a refresh token for a new access token. Access tokens expire in 30 minutes. Refresh tokens expire in 7 days.

**Request body**

| Field | Type | Required |
|---|---|---|
| `refresh` | string | Yes |

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response — 200 OK**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `TOKEN_INVALID` | 401 | Token is malformed or has been blacklisted. |
| `TOKEN_EXPIRED` | 401 | Refresh token has expired. User must log in again. |

---

### 1.4 Logout

**`POST /auth/logout/`** — JWT required

Blacklists the refresh token. The access token will continue to work until it expires naturally (30 minutes).

**Request body**

| Field | Type | Required |
|---|---|---|
| `refresh` | string | Yes |

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response — 204 No Content**

No body.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `VALIDATION_ERROR` | 400 | `refresh` field missing. |
| `TOKEN_INVALID` | 401 | Token is already invalid or expired. |

---

## 2. Communities

Communities allow groups of users to share quizzes. Each community gets a unique 12-character join code on creation. The creator is automatically added as a member.

### 2.1 List my communities

**`GET /communities/`** — JWT required

Returns all communities the current user is a member of. Cursor paginated.

**Response — 200 OK**

```json
{
  "next": "http://localhost:8000/api/v1/communities/?cursor=...",
  "previous": null,
  "results": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Backend Study Group",
      "description": "A group for backend developers",
      "join_code": "ABC123XYZ789",
      "creator_name": "ada_codes",
      "is_member": true,
      "member_count": 12,
      "created_at": "2025-03-19T10:30:00Z"
    }
  ]
}
```

---

### 2.2 Create a community

**`POST /communities/`** — JWT required

Creates a new community. The authenticated user becomes creator and first member. `join_code` is auto-generated and cannot be set manually.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Community display name. |
| `description` | string | No | Optional description. |

```json
{
  "name": "Backend Study Group",
  "description": "A group for backend developers"
}
```

**Response — 201 Created**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Backend Study Group",
  "description": "A group for backend developers",
  "join_code": "ABC123XYZ789",
  "creator_name": "ada_codes",
  "is_member": true,
  "member_count": 1,
  "created_at": "2025-03-19T10:30:00Z"
}
```

---

### 2.3 Retrieve a community

**`GET /communities/{id}/`** — JWT required

Returns a single community. User must be a member.

**Response — 200 OK**

Same shape as the list item above.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `NOT_FOUND` | 404 | Community does not exist or user is not a member. |

---

### 2.4 Update a community

**`PATCH /communities/{id}/`** — JWT required

Updates `name` or `description`. All fields optional.

**Request body**

```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response — 200 OK**

Same shape as the create response.

---

### 2.5 Delete a community

**`DELETE /communities/{id}/`** — JWT required

Deletes the community permanently.

**Response — 204 No Content**

---

### 2.6 Join a community

**`POST /communities/join/`** — JWT required

Joins a community using its join code. The join code is case-insensitive.

**Request body**

| Field | Type | Required |
|---|---|---|
| `join_code` | string | Yes |

```json
{
  "join_code": "ABC123XYZ789"
}
```

**Response — 200 OK**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Backend Study Group",
  "description": "A group for backend developers",
  "join_code": "ABC123XYZ789",
  "creator_name": "ada_codes",
  "is_member": true,
  "member_count": 13,
  "created_at": "2025-03-19T10:30:00Z"
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `NOT_FOUND` | 404 | No community found with that join code. |
| `VALIDATION_ERROR` | 400 | Already a member of this community. |

---

## 3. Quiz Requests

Quiz generation is asynchronous. Submitting a request returns immediately. The client polls the status endpoint until generation is complete.

**Status lifecycle:** `pending` → `processing` → `completed` or `failed`

### 3.1 Submit a quiz request

**`POST /quizzes/quiz-requests/`** — JWT required

Submits a quiz generation request. Returns `202 Accepted` immediately. A background task handles the AI generation.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `topic` | string | Yes | Subject of the quiz. Be specific for better results. Max 255 chars. |
| `difficulty` | string | Yes | One of: `easy`, `medium`, `hard` |
| `question_count` | integer | Yes | Number of questions. Min: 1, Max: 50. |
| `community` | UUID | No | Community to scope this quiz to. User must be a member of the community. Omit for a personal quiz. |

```json
{
  "topic": "Python decorators",
  "difficulty": "medium",
  "question_count": 5
}
```

```json
{
  "topic": "Django ORM",
  "difficulty": "hard",
  "question_count": 10,
  "community": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Response — 202 Accepted**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "topic": "Python decorators",
  "difficulty": "medium",
  "question_count": 5,
  "status": "pending",
  "failure_reason": null,
  "quiz_id": null,
  "created_at": "2025-03-19T10:30:00Z"
}
```

`quiz_id` is `null` until generation completes.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Invalid difficulty, question_count out of range, or user is not a member of the specified community. |

---

### 3.2 Poll quiz request status

**`GET /quizzes/quiz-requests/{id}/`** — JWT required

Returns the current status of a generation request. Poll every 2 seconds until `status` is `completed` or `failed`.

**Response — 200 OK — while generating**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "topic": "Python decorators",
  "difficulty": "medium",
  "question_count": 5,
  "status": "processing",
  "failure_reason": null,
  "quiz_id": null,
  "created_at": "2025-03-19T10:30:00Z"
}
```

**Response — 200 OK — on success**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "topic": "Python decorators",
  "difficulty": "medium",
  "question_count": 5,
  "status": "completed",
  "failure_reason": null,
  "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "created_at": "2025-03-19T10:30:00Z"
}
```

**Response — 200 OK — on failure**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "topic": "Python decorators",
  "difficulty": "medium",
  "question_count": 5,
  "status": "failed",
  "failure_reason": "AI service returned an invalid response after 3 attempts.",
  "quiz_id": null,
  "created_at": "2025-03-19T10:30:00Z"
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `NOT_FOUND` | 404 | Request does not exist or belongs to another user. |

---

### 3.3 List quiz requests

**`GET /quizzes/quiz-requests/`** — JWT required

Returns the current user's generation requests in reverse chronological order. Cursor paginated.

**Response — 200 OK**

```json
{
  "next": "http://localhost:8000/api/v1/quizzes/quiz-requests/?cursor=...",
  "previous": null,
  "results": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "topic": "Python decorators",
      "difficulty": "medium",
      "question_count": 5,
      "status": "completed",
      "failure_reason": null,
      "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "created_at": "2025-03-19T10:30:00Z"
    }
  ]
}
```

---

## 4. Quizzes

### 4.1 List quizzes

**`GET /quizzes/`** — JWT required

Returns published quizzes accessible to the current user. Cursor paginated.

**Visibility rules:**
- Community quizzes are visible to members of that community.
- Personal quizzes (no community) are visible only to the user who created them.

**Query parameters**

| Parameter | Type | Notes |
|---|---|---|
| `topic` | string | Exact match filter. |
| `difficulty` | string | One of: `easy`, `medium`, `hard` |
| `community` | UUID or `personal` | Filter by community UUID, or pass `personal` to see only personal quizzes. |
| `cursor` | string | Cursor from previous response for next page. |

**Response — 200 OK**

```json
{
  "next": "http://localhost:8000/api/v1/quizzes/?cursor=...",
  "previous": null,
  "results": [
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "title": "Quiz on Python decorators",
      "topic": "Python decorators",
      "difficulty": "medium",
      "time_limit_secs": 300,
      "community": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "community_name": "Backend Study Group",
      "created_at": "2025-03-19T10:30:00Z"
    }
  ]
}
```

`community` and `community_name` are `null` for personal quizzes. `time_limit_secs` is calculated as `question_count * 60` at generation time.

---

### 4.2 Get quiz detail

**`GET /quizzes/{id}/`** — JWT required

Returns the full quiz with all questions and options. Correct answers are never included in this response. Cached for 1 hour.

**Response — 200 OK**

```json
{
  "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "title": "Quiz on Python decorators",
  "topic": "Python decorators",
  "difficulty": "medium",
  "time_limit_secs": 300,
  "questions": [
    {
      "id": "c72e4f3a-1234-5678-abcd-ef0123456789",
      "body": "What does the @property decorator do in Python?",
      "question_type": "multiple_choice",
      "order": 1,
      "points": 10,
      "options": [
        {
          "id": "opt-1-uuid",
          "body": "Defines a method as a read-only attribute",
          "order": 1
        },
        {
          "id": "opt-2-uuid",
          "body": "Makes a method static",
          "order": 2
        },
        {
          "id": "opt-3-uuid",
          "body": "Creates a class variable",
          "order": 3
        },
        {
          "id": "opt-4-uuid",
          "body": "Prevents method overriding",
          "order": 4
        }
      ]
    }
  ]
}
```

Note: `is_correct` is intentionally absent from all option objects on this endpoint.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `NOT_FOUND` | 404 | Quiz does not exist, is unpublished, is deleted, or is not accessible to the current user. |

---

### 4.3 Get quiz analytics

**`GET /quizzes/{id}/analytics/`** — JWT required

Returns pre-computed aggregate statistics for the quiz. Cached for 15 minutes.

**Access:** quiz creator, any member of the quiz's community, or admin.

**Response — 200 OK**

```json
{
  "total_attempts": 24,
  "avg_score_pct": 68.5,
  "avg_completion_secs": 187,
  "question_stats": {
    "c72e4f3a-1234-5678-abcd-ef0123456789": {
      "correct_rate_pct": 83.33,
      "avg_time_secs": 22
    },
    "d83f5a4b-5678-90ab-cdef-012345678901": {
      "correct_rate_pct": 41.67,
      "avg_time_secs": 38
    }
  }
}
```

`question_stats` keys are question UUIDs. `correct_rate_pct` is the percentage of attempts that answered that question correctly. `avg_time_secs` is the average time from attempt start to when that question was answered.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `PERMISSION_DENIED` | 403 | User is not the quiz creator, not a community member, and not an admin. |
| `NOT_FOUND` | 404 | Quiz does not exist. |

---

## 5. Attempts

### Attempt lifecycle

```
POST /attempts/         →   status: in_progress
PATCH /attempts/{id}/answer/   →   save answers (repeatable)
POST /attempts/{id}/submit/    →   status: submitted, score calculated
```

Each user can have only one attempt per quiz. Skipped questions are automatically recorded as incorrect on submission.

---

### 5.1 Start an attempt

**`POST /attempts/`** — JWT required

Creates a new attempt for the given quiz.

**Request body**

| Field | Type | Required |
|---|---|---|
| `quiz_id` | UUID | Yes |

```json
{
  "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

**Response — 201 Created**

```json
{
  "id": "e5a1f2b3-c4d5-6789-abcd-ef0123456789",
  "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "in_progress",
  "score": 0,
  "max_score": 0,
  "score_percentage": 0.0,
  "started_at": "2025-03-19T10:30:00Z",
  "submitted_at": null,
  "answers": []
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `VALIDATION_ERROR` | 400 | `quiz_id` missing. |
| `NOT_FOUND` | 404 | Quiz does not exist. |
| `QUIZ_NOT_PUBLISHED` | 403 | Quiz exists but is not published. |
| `PERMISSION_DENIED` | 403 | Community quiz and user is not a member. Or personal quiz created by someone else. |
| `DUPLICATE_ATTEMPT` | 409 | User already has an attempt for this quiz. |

---

### 5.2 Save an answer

**`PATCH /attempts/{id}/answer/`** — JWT required (attempt owner only)

Saves or updates the answer for a single question. Can be called multiple times for the same question — the last call wins. Use this for auto-saving as the user selects options.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `question_id` | UUID | Yes | Must belong to the quiz being attempted. |
| `option_id` | UUID | Yes | Must belong to the question. |

```json
{
  "question_id": "c72e4f3a-1234-5678-abcd-ef0123456789",
  "option_id": "opt-1-uuid"
}
```

**Response — 200 OK**

```json
{
  "message": "Answer recorded.",
  "answered_at": "2025-03-19T10:32:15Z"
}
```

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `ATTEMPT_SUBMITTED` | 403 | Attempt has already been submitted. Answers are locked. |
| `NOT_FOUND` | 404 | Attempt, question, or option not found. |
| `VALIDATION_ERROR` | 400 | Question does not belong to this quiz's questions, or option does not belong to this question. |
| `PERMISSION_DENIED` | 403 | Attempt belongs to a different user. |

---

### 5.3 Submit an attempt

**`POST /attempts/{id}/submit/`** — JWT required (attempt owner only)

Locks the attempt, scores all answers, creates ghost answer records for skipped questions, and triggers an analytics update in the background. Returns the full result immediately.

No request body needed.

**Response — 200 OK**

```json
{
  "id": "e5a1f2b3-c4d5-6789-abcd-ef0123456789",
  "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "submitted",
  "score": 30,
  "max_score": 50,
  "score_percentage": 60.0,
  "started_at": "2025-03-19T10:30:00Z",
  "submitted_at": "2025-03-19T10:38:00Z",
  "answers": [
    {
      "id": "answer-uuid",
      "question_id": "c72e4f3a-1234-5678-abcd-ef0123456789",
      "question_body": "What does the @property decorator do in Python?",
      "selected_option_id": "opt-1-uuid",
      "selected_option_body": "Defines a method as a read-only attribute",
      "correct_option_id": "opt-1-uuid",
      "correct_option_body": "Defines a method as a read-only attribute",
      "is_correct": true,
      "points_awarded": 10
    },
    {
      "id": "answer-uuid-2",
      "question_id": "d83f5a4b-5678-90ab-cdef-012345678901",
      "question_body": "Which decorator makes a method belong to the class?",
      "selected_option_id": null,
      "selected_option_body": null,
      "correct_option_id": "opt-correct-uuid",
      "correct_option_body": "@classmethod",
      "is_correct": false,
      "points_awarded": 0
    }
  ]
}
```

`correct_option_id` and `correct_option_body` are always revealed on submission, including for skipped questions. `selected_option_id` is `null` for skipped questions.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `ATTEMPT_SUBMITTED` | 403 | Attempt has already been submitted. |
| `NOT_FOUND` | 404 | Attempt not found. |
| `PERMISSION_DENIED` | 403 | Attempt belongs to a different user. |

---

### 5.4 Get attempt detail

**`GET /attempts/{id}/`** — JWT required (attempt owner only)

Returns the current state of an attempt. Response content varies by status.

**Response — 200 OK — while in progress**

Correct answers are omitted. Only recorded answers are returned.

```json
{
  "id": "e5a1f2b3-c4d5-6789-abcd-ef0123456789",
  "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "in_progress",
  "score": 0,
  "max_score": 0,
  "score_percentage": 0.0,
  "started_at": "2025-03-19T10:30:00Z",
  "submitted_at": null,
  "answers": [
    {
      "question_id": "c72e4f3a-1234-5678-abcd-ef0123456789",
      "selected_option_id": "opt-1-uuid",
      "answered_at": "2025-03-19T10:32:15Z"
    }
  ]
}
```

**Response — 200 OK — after submission**

Full result with correct answers revealed. Same shape as the submit response above.

**Errors**

| Code | HTTP | Cause |
|---|---|---|
| `NOT_FOUND` | 404 | Attempt not found. |
| `PERMISSION_DENIED` | 403 | Attempt belongs to a different user. |

---

## 6. User

### 6.1 Attempt history

**`GET /users/me/history/`** — JWT required

Returns the current user's completed attempts in reverse chronological order. Cursor paginated.

**Query parameters**

| Parameter | Type | Notes |
|---|---|---|
| `cursor` | string | Cursor from previous response for next page. |

**Response — 200 OK**

```json
{
  "next": "http://localhost:8000/api/v1/users/me/history/?cursor=...",
  "previous": null,
  "results": [
    {
      "id": "e5a1f2b3-c4d5-6789-abcd-ef0123456789",
      "quiz_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "quiz_title": "Quiz on Python decorators",
      "quiz_topic": "Python decorators",
      "topic": "Python decorators",
      "difficulty": "medium",
      "score": 30,
      "max_score": 50,
      "score_percentage": 60.0,
      "submitted_at": "2025-03-19T10:38:00Z"
    }
  ]
}
```

---

### 6.2 Performance stats

**`GET /users/me/performance/`** — JWT required

Returns aggregated performance statistics for the current user across all completed attempts. Cached for 5 minutes.

**Response — 200 OK**

```json
{
  "total_attempts": 12,
  "avg_score_pct": 72.5,
  "by_topic": [
    {
      "topic": "Python decorators",
      "total_attempts": 3,
      "avg_score_pct": 80.0
    },
    {
      "topic": "Django ORM",
      "total_attempts": 5,
      "avg_score_pct": 64.0
    }
  ],
  "by_difficulty": [
    {
      "difficulty": "easy",
      "total_attempts": 4,
      "avg_score_pct": 91.0
    },
    {
      "difficulty": "medium",
      "total_attempts": 6,
      "avg_score_pct": 68.0
    },
    {
      "difficulty": "hard",
      "total_attempts": 2,
      "avg_score_pct": 45.0
    }
  ],
  "best_topic": "Python decorators",
  "weakest_topic": "Django ORM"
}
```

Returns zeroed data if the user has no completed attempts:

```json
{
  "total_attempts": 0,
  "avg_score_pct": 0,
  "by_topic": [],
  "by_difficulty": [],
  "best_topic": null,
  "weakest_topic": null
}
```

---

## 7. Admin

All admin endpoints require a user with `role = admin`. Requests from authenticated non-admin users return `403 PERMISSION_DENIED`.

### 7.1 List all quizzes

**`GET /admin/quizzes/`** — Admin JWT required

Returns all quizzes including unpublished and soft-deleted ones. Ordered by `created_at` descending. Cursor paginated.

**Response — 200 OK**

```json
{
  "next": "http://localhost:8000/api/v1/admin/quizzes/?cursor=...",
  "previous": null,
  "results": [
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "title": "Quiz on Python decorators",
      "topic": "Python decorators",
      "difficulty": "medium",
      "is_published": true,
      "deleted_at": null,
      "created_at": "2025-03-19T10:30:00Z"
    }
  ]
}
```

---

### 7.2 Get a quiz

**`GET /admin/quizzes/{id}/`** — Admin JWT required

Returns a single quiz. Same response shape as the list item.

---

### 7.3 Update a quiz

**`PATCH /admin/quizzes/{id}/`** — Admin JWT required

Updates a quiz. Only `is_published` can be changed. Invalidates the quiz detail cache on save.

**Request body**

| Field | Type | Notes |
|---|---|---|
| `is_published` | boolean | `true` to publish, `false` to unpublish. |

```json
{
  "is_published": false
}
```

**Response — 200 OK**

Same shape as the list item.

---

### 7.4 Delete a quiz (soft delete)

**`DELETE /admin/quizzes/{id}/`** — Admin JWT required

Soft deletes the quiz by setting `deleted_at` to the current timestamp and `is_published` to `false`. The record is not removed from the database. Invalidates the quiz detail cache.

**Response — 204 No Content**

---

## 8. Error Reference

Full list of error codes returned by the API:

| Code | HTTP | Description |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Request body failed validation. Check `details` for field-level messages. |
| `INVALID_CREDENTIALS` | 401 | Email or password is incorrect. |
| `TOKEN_INVALID` | 401 | JWT is missing, malformed, or blacklisted. |
| `TOKEN_EXPIRED` | 401 | JWT has expired. Use the refresh endpoint to get a new access token. |
| `PERMISSION_DENIED` | 403 | Authenticated but not authorised for this resource. |
| `QUIZ_NOT_PUBLISHED` | 403 | Quiz exists but is not published. |
| `ATTEMPT_SUBMITTED` | 403 | Attempt has already been submitted. Answers cannot be changed. |
| `NOT_FOUND` | 404 | Resource does not exist or is not visible to the current user. |
| `DUPLICATE_ATTEMPT` | 409 | User already has an attempt for this quiz. Only one attempt per quiz is allowed. |

---

## 9. Pagination

All list endpoints use cursor-based pagination. There is no page number — use the `next` URL from the response to fetch the following page.

**Response structure**

```json
{
  "next": "http://localhost:8000/api/v1/quizzes/?cursor=cD0yMDI1LTAz...",
  "previous": null,
  "results": []
}
```

`next` is `null` when there are no more pages. `previous` is `null` when on the first page.

**Page size:** 10 results per page (default).

To fetch the next page, make a GET request to the full `next` URL as returned — do not construct cursor values manually.
