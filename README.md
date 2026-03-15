# EMS - Education Management System

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│                    Communicates via RESTful API                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI - Python)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Auth JWT   │  │  RBAC Roles  │  │   Business Logic     │ │
│  │  Middleware  │  │  Middleware  │  │   (Services)         │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
          ┌──────────────────────┴──────────────────────┐
          ▼                                             ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│   Primary Database      │               │   Cache (Redis)         │
│   MSSQL Server         │               │   - Session Storage     │
│   (ACID Compliant)     │               │   - JWT Blacklist      │
└─────────────────────────┘               │   - Query Cache        │
                                          └─────────────────────────┘
```

---

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | High-performance async API framework |
| Language | Python 3.13 | Modern async/await support |
| ORM | SQLAlchemy | Database abstraction layer |
| Auth | JWT (PyJWT) | Token-based authentication |
| Database | MSSQL | Primary transactional database |
| Cache | Redis | Session & token management |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js | React-based SPA/SSR |
| Language | TypeScript | Type safety |
| HTTP Client | Axios | API communication |

---

## Architecture Layers

```
┌────────────────────────────────────────────┐
│         Controllers (API Endpoints)          │
│   @app.get(), @app.post() etc.             │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│            Services (Business Logic)         │
│   Validation, Orchestration, Computation    │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│           Repositories (Data Access)        │
│   SQLAlchemy Queries, CRUD Operations       │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│              Entities (Models)              │
│   SQLAlchemy ORM Models → DB Tables        │
└────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `users` | Authentication accounts (linked to teachers/students) |
| `teachers` | Teacher profiles and employment info |
| `students` | Student profiles and enrollment |
| `classrooms` | Class definitions |
| `student_class_enrollments` | Student-class relationships |
| `subjects` | Subject catalog |
| `class_subjects` | Subject assignments to classes |
| `grade_components` | Grade structure (midterm, final, homework...) |
| `student_grades` | Individual student scores |
| `salary_grades` | Teacher salary scales |
| `bonus_policies` | Bonus/incentive rules |
| `monthly_payroll` | Monthly salary calculations |

---

## Authentication Flow

```
1. User Login
   │
   ▼
2. Validate credentials against users table
   │
   ▼
3. Generate JWT (access_token + refresh_token)
   │
   ▼
4. Store token metadata in Redis (blacklist support)
   │
   ▼
5. Subsequent requests include: Authorization: Bearer <token>
   │
   ▼
6. Middleware validates token, extracts user_id + role
   │
   ▼
7. Role-based access control (RBAC)
```

### JWT Token Structure
```python
{
  "sub": "user_id",           # User ID
  "role": "teacher",          # RBAC role
  "teacher_id": 4,            # Link to teacher profile
  "exp": 1234567890,          # Expiration
  "type": "access",           # Token type
  "jti": "unique-id"         # Token ID (for blacklist)
}
```

---

## Project Structure

```
EMS_backend/
├── app/
│   ├── core/                 # Core utilities
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── security.py       # JWT, password hashing
│   │   ├── dependencies.py   # Auth dependencies
│   │   └── exceptions/       # Custom exceptions
│   │
│   ├── modules/              # Feature modules
│   │   ├── auth/            # Authentication
│   │   │   ├── entity.py    # User model
│   │   │   ├── dto.py       # Request/Response schemas
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── controller.py
│   │   │
│   │   ├── teacher/         # Teacher management
│   │   ├── student/         # Student management
│   │   ├── classroom/       # Class management
│   │   ├── grading/         # Grade management
│   │   ├── salary/          # Payroll system
│   │   └── ...
│   │
│   ├── main.py              # FastAPI application
│   └── utils/               # Utilities (email, etc.)
│
├── alembic/                 # Database migrations
├── tests/                   # Unit & integration tests
└── .env                    # Configuration
```

---

## API Communication Pattern

### Request Format
```json
{
  "key1": "value1",
  "key2": "value2"
}
```

### Response Format (Standardized)
```json
// Success
{
  "code": 200,
  "message": "Success",
  "detail": "Operation completed",
  "data": { ... }
}

// Error
{
  "code": 400,
  "message": "Error",
  "detail": "Error description",
  "data": null
}
```

---

## Deployment

### Server Requirements
- 4 vCPU, 8GB RAM, 100GB SSD
- Windows Server / Linux

### Run Development Server
```bash
cd d:/EMS_backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Setup (Recommended)
```
Nginx (Reverse Proxy)
    │
    ▼
Gunicorn + Uvicorn Workers
    │
    ▼
FastAPI Application
    │
    ├─────────────────┐
    ▼                 ▼
MSSQL            Redis
```

---

## Key Design Principles

1. **Clean Architecture**: Separation of concerns (Controller → Service → Repository → Entity)
2. **Async-First**: All I/O operations use async/await for maximum throughput
3. **ACID Transactions**: Critical operations (grading, payroll) use database transactions
4. **JWT stateless Auth**: Scalable authentication with Redis token blacklist
5. **Type Safety**: Pydantic models for request/response validation
