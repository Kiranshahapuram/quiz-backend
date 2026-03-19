# 🧬 QuizQuest.AI - API Documentation (v1)

**Base URL**: `http://127.0.0.1:8000/api/v1`  
**Auth**: JWT Bearer (`Authorization: Bearer <token>`)  
**Format**: JSON

---

## 🔐 1. Authentication

### **User Registration**
`POST /auth/register/`
```json
{
  "email": "user@example.com",
  "username": "alias_01",
  "password": "Password123!",
  "full_name": "Full Name"
}
```
**Success**: `201 Created`

### **User Login**
`POST /auth/login/`
```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```
**Response**: `{ "access": "...", "refresh": "..." }`

---

## 🧠 2. Quizzes (Neural Content)

### **Request New Quiz (AI Generation)**
`POST /quizzes/quiz-requests/`
```json
{
  "topic": "FastAPI",
  "difficulty": "medium",
  "question_count": 5
}
```
**Status**: `202 Accepted` (Worker is generating)

### **List All Quizzes**
`GET /quizzes/`
```json
[
  { "id": "uuid", "topic": "...", "difficulty": "...", "title": "..." }
]
```

### **Quiz Content (Questions + Options)**
`GET /quizzes/{quiz_id}/` (Questions are randomized)

### **Quiz Global Analytics**
`GET /quizzes/{quiz_id}/analytics/`
**Response**: Global accuracy, avg time, and question-wise correctness rates.

---

## 🎮 3. Game Process (Attempts)

### **Step 1: Start Attempt**
`POST /attempts/`
```json
{ "quiz_id": "uuid" }
```
**Response**: `{ "id": "uuid", "status": "in_progress" }`

### **Step 2: Answer Question**
`PATCH /attempts/{attempt_id}/answer/`  
(Can be called multiple times for different questions)
```json
{
  "question_id": "uuid",
  "option_id": "uuid"
}
```
**Status**: `204 No Content` (Updated successfully)

### **Step 3: Submit & Finalize**
`POST /attempts/{attempt_id}/submit/`
**Response**: Returns final score and **full breakdown** containing correct/incorrect answers.

---

## 📈 4. User Profile & Tracking

### **Global Performance Stats**
`GET /users/me/performance/`  
Provides accuracy by topic, difficulty, best/weakest subjects.

### **Historical Log**
`GET /users/me/history/`  
Paginated list of past quiz sessions with scores and topics.

---

## 🛠️ Error Codes
- **400 Bad Request**: Validation error (invalid topic, etc.)
- **401 Unauthorized**: Token expired or missing.
- **404 Not Found**: Invalid ID.
- **429 Too Many Requests**: Rate limits exceeded.
