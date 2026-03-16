# EMS - API Reference

> Base URL: `http://localhost:8000/api/v1`
> 
> All responses follow the standard APIResponse format:
> ```json
> { "code": 200, "message": "Success", "detail": "...", "data": { ... }, "errors": null }
> ```

---

## HTTP Status Codes

| Code | Message | Description |
|------|---------|-------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required or token invalid |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Validation Error | Invalid input data |
| 500 | Internal Server Error | Server error |

---

## Common Error Messages

| Error | Detail | Description |
|-------|--------|-------------|
| Invalid Credentials | The provided username or password is incorrect | Wrong username/email or password |
| Account Disabled | Your account has been disabled. Please contact administrator. | User account is deactivated |
| Token Invalid | Invalid or malformed token | JWT token is invalid |
| Token Expired | Token has expired. Please login again. | JWT token has expired |
| Token Blacklisted | This token has been revoked. Please login again. | Token was logged out |
| Not Found | {resource} not found | Requested resource doesn't exist |
| Already Exists | {resource} already exists | Duplicate resource |
| Validation Error | {detail} | Input validation failed |

---

## Authentication & Authorization

- **Protected endpoints** require header: `Authorization: Bearer <access_token>`
- **Roles**: `admin`, `teacher`, `accountant`

| Role | Access |
|------|--------|
| admin | Full access to all modules |
| teacher | Teacher Portal, Grading |
| accountant | Salary module |

---

## Endpoints Summary

| Module | Prefix | Description |
|--------|--------|-------------|
| System | `/` | Health check |
| Auth | `/auth` | Login, logout, password management |
| Bootstrap | `/auth/init` | Initial admin creation |
| Students | `/students` | Student management |
| Teachers | `/teachers` | Teacher management |
| Classrooms | `/classrooms` | Class & enrollment management |
| Grading | `/grading` | Subjects, grades, reports |
| Salary | `/salary` | Payroll, bonuses |
| Dashboard | `/dashboard` | Statistics |
| Lookups | `/lookups` | Dropdown data |
| Teacher Portal | `/teacher` | Teacher workspace |
| Admin | `/admin` | Admin timetable & attendance |

---

## 1. System

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "database": "primary (MSSQL)"
  }
}
```

---

## 2. Auth

Base path: `/api/v1/auth`

### POST `/login`
Login with email and password.

**Request:**
```json
{
  "email": "doanh.nguyen@eiu.edu.vn",
  "password": "yourpassword"
}
```

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Login success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "role": "teacher",
    "user_id": 2,
    "teacher_id": 4
  },
  "errors": null
}
```

**Response (401 - Invalid Credentials):**
```json
{
  "code": 401,
  "message": "Invalid Credentials",
  "detail": "The provided username or password is incorrect",
  "data": null,
  "errors": null
}
```

**Response (401 - Account Disabled):**
```json
{
  "code": 401,
  "message": "Account Disabled",
  "detail": "Your account has been disabled. Please contact administrator.",
  "data": null,
  "errors": null
}
```

---

### POST `/refresh`
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Token refreshed",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "role": "teacher",
    "user_id": 2,
    "teacher_id": 4
  },
  "errors": null
}
```

**Response (401 - Token Invalid):**
```json
{
  "code": 401,
  "message": "Token Invalid",
  "detail": "Invalid or malformed token",
  "data": null,
  "errors": null
}
```

**Response (401 - Token Expired):**
```json
{
  "code": 401,
  "message": "Token Expired",
  "detail": "Token has expired. Please login again.",
  "data": null,
  "errors": null
}
```

**Response (401 - Token Blacklisted):**
```json
{
  "code": 401,
  "message": "Token Blacklisted",
  "detail": "This token has been revoked. Please login again.",
  "data": null,
  "errors": null
}
```

---

### POST `/logout`
Logout and blacklist the token.

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "refresh"
}
```

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Logged out successfully",
  "data": null,
  "errors": null
}
```

---

### POST `/forgot-password`
Request password reset via email.

**Request:**
```json
{
  "email": "doanh.nguyen@eiu.edu.vn"
}
```

**Response (200 - Always returned for security):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu.",
  "data": {
    "message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."
  },
  "errors": null
}
```

---

### POST `/reset-password`
Reset password with token (token expires in 30 minutes).

**Request:**
```json
{
  "token": "abc123...",
  "new_password": "newpassword123"
}
```

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Đặt lại mật khẩu thành công",
  "data": {
    "message": "Đặt lại mật khẩu thành công"
  },
  "errors": null
}
```

**Response (422 - Validation Error):**
```json
{
  "code": 422,
  "message": "Validation Error",
  "detail": "Token không hợp lệ hoặc đã hết hạn",
  "data": null,
  "errors": null
}
```

**Response (422 - Password too short):**
```json
{
  "code": 422,
  "message": "Validation Error",
  "detail": "Mật khẩu phải có ít nhất 6 ký tự",
  "data": null,
  "errors": null
}
```

---

### POST `/change-password` (auth required)
Change password when logged in.

**Request:**
```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword123"
}
```

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Đổi mật khẩu thành công",
  "data": null,
  "errors": null
}
```

**Response (401 - Wrong old password):**
```json
{
  "code": 401,
  "message": "Invalid Credentials",
  "detail": "Mật khẩu cũ không đúng",
  "data": null,
  "errors": null
}
```

**Response (422 - Password too short):**
```json
{
  "code": 422,
  "message": "Validation Error",
  "detail": "Mật khẩu phải có ít nhất 6 ký tự",
  "data": null,
  "errors": null
}
```

---

### POST `/users` (admin)
Create a new user account.

**Request:**
```json
{
  "username": "doanh.nguyen@eiu.edu.vn",
  "password": "password123",
  "role": "teacher",
  "teacher_id": 4
}
```

**Response (201 - Created):**
```json
{
  "code": 201,
  "message": "Created",
  "detail": "User created successfully",
  "data": {
    "id": 5,
    "username": "doanh.nguyen@eiu.edu.vn",
    "role": "teacher",
    "teacher_id": 4,
    "is_active": true,
    "last_login_at": null
  },
  "errors": null
}
```

**Response (409 - Already Exists):**
```json
{
  "code": 409,
  "message": "Conflict",
  "detail": "User already exists",
  "data": null,
  "errors": null
}
```

**Response (422 - Validation Error):**
```json
{
  "code": 422,
  "message": "Validation Error",
  "detail": "teacher_id is required for teacher role",
  "data": null,
  "errors": null
}
```

---

### GET `/users` (admin)
List users with pagination and filters.

**Query params:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)
- `role` - Filter by role (admin, teacher, accountant, student)
- `is_active` - Filter by active status (true/false)

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Users retrieved",
  "data": {
    "items": [
      {
        "id": 1,
        "username": "admin@eiu.edu.vn",
        "role": "admin",
        "teacher_id": null,
        "is_active": true,
        "last_login_at": "2026-03-15T10:00:00"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "errors": null
}
```

---

### GET `/users/{user_id}` (admin)
Get user details.

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "User retrieved",
  "data": {
    "id": 2,
    "username": "doanh.nguyen@eiu.edu.vn",
    "role": "teacher",
    "teacher_id": 4,
    "is_active": true,
    "last_login_at": "2026-03-15T10:00:00"
  },
  "errors": null
}
```

**Response (404 - Not Found):**
```json
{
  "code": 404,
  "message": "Not Found",
  "detail": "User not found",
  "data": null,
  "errors": null
}
```

---

### PATCH `/users/{user_id}` (admin)
Update user.

**Request:**
```json
{
  "role": "accountant",
  "is_active": false
}
```

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "User updated successfully",
  "data": {
    "id": 2,
    "username": "doanh.nguyen@eiu.edu.vn",
    "role": "accountant",
    "teacher_id": 4,
    "is_active": false,
    "last_login_at": "2026-03-15T10:00:00"
  },
  "errors": null
}
```

---

### POST `/teachers/{teacher_id}/account` (admin)
Create account for a teacher.

**Request:**
```json
{
  "send_email": true
}
```

**Response (201 - Created):**
```json
{
  "code": 201,
  "message": "Created",
  "detail": "Tài khoản Giáo viên đã được tạo",
  "data": {
    "user_id": 3,
    "teacher_id": 5,
    "teacher_code": "TCHR001",
    "teacher_name": "Nguyen Van A",
    "email": "nguyenvana@eiu.edu.vn",
    "username": "nguyenvana@eiu.edu.vn",
    "temp_password": "a1b2c3d4",
    "email_sent": true,
    "must_change_password": true
  },
  "errors": null
}
```

**Response (409 - Already Exists):**
```json
{
  "code": 409,
  "message": "Conflict",
  "detail": "User already exists",
  "data": null,
  "errors": null
}
```

**Response (404 - Not Found):**
```json
{
  "code": 404,
  "message": "Not Found",
  "detail": "Teacher not found",
  "data": null,
  "errors": null
}
```

---

### DELETE `/users/{user_id}` (admin)
Permanently delete user.

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "User deleted successfully",
  "data": null,
  "errors": null
}
```

---

### POST `/users/{user_id}/deactivate` (admin)
Deactivate user account.

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "User deactivated successfully",
  "data": {
    "id": 2,
    "username": "doanh.nguyen@eiu.edu.vn",
    "role": "teacher",
    "is_active": false
  },
  "errors": null
}
```

---

### POST `/users/{user_id}/reactivate` (admin)
Reactivate user account.

**Response (200 - Success):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "User reactivated successfully",
  "data": {
    "id": 2,
    "username": "doanh.nguyen@eiu.edu.vn",
    "role": "teacher",
    "is_active": true
  },
  "errors": null
}
```

---

## 3. Bootstrap

Base path: `/api/v1/auth/init`

### POST `/admin`
Create first admin user (for system initialization).

**Request:**
```json
{
  "secret": "ems-bootstrap-secret-change-me",
  "username": "admin@eiu.edu.vn",
  "password": "yourpassword"
}
```

**Response (201 - Created):**
```json
{
  "code": 201,
  "message": "Created",
  "detail": "Admin user created successfully",
  "data": {
    "id": 1,
    "username": "admin@eiu.edu.vn",
    "role": "admin",
    "message": "Admin user created successfully"
  },
  "errors": null
}
```

**Response (409 - Already Exists):**
```json
{
  "code": 409,
  "message": "Conflict",
  "detail": "Admin user already exists",
  "data": null,
  "errors": null
}
```

**Response (401 - Invalid Secret):**
```json
{
  "code": 401,
  "message": "Unauthorized",
  "detail": "Invalid bootstrap secret",
  "data": null,
  "errors": null
}
```

---

### GET `/status`
Check if system is initialized.

**Response (200 - Not Initialized):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "System not initialized",
  "data": {
    "initialized": false
  },
  "errors": null
}
```

**Response (200 - Already Initialized):**
```json
{
  "code": 200,
  "message": "Success",
  "detail": "System already initialized",
  "data": {
    "initialized": true
  },
  "errors": null
}
```

---

## 4. Students

Base path: `/api/v1/students`

### POST `/` (admin)
Create new student.

### GET `/` (admin)
List students with pagination and filters.

**Query params:**
- `search` - Search by code or name
- `academic_status` - Filter by status
- `has_enrollment` - Filter enrolled/not enrolled
- `classroom_id` - Filter by classroom
- `page`, `page_size` - Pagination

### GET `/{student_code}` (admin)
Get student details with enrollments.

### PATCH `/{student_code}` (admin)
Update student profile.

### PATCH `/{student_code}/status` (admin)
Update academic status.

**Valid transitions:**
- `active` → `preserved` | `suspended` | `graduated`
- `preserved` → `active` | `suspended`
- `suspended` → `active`
- `graduated` → (terminal)

### DELETE `/{student_code}` (admin)
Soft-delete student.

---

## 5. Teachers

Base path: `/api/v1/teachers`

### POST `/` (admin)
Create new teacher.

### GET `/` (admin)
List teachers with pagination and filters.

**Query params:**
- `search` - Search by code, name, or email
- `employment_status` - Filter by status
- `department` - Filter by department
- `specialization` - Filter by specialization
- `page`, `page_size` - Pagination

### GET `/{teacher_code}` (admin)
Get teacher details with teaching assignments.

### PATCH `/{teacher_code}` (admin)
Partially update teacher profile.

### PATCH `/{teacher_code}/status` (admin)
Update employment status.

**Valid transitions:**
- `active` → `on_leave` | `resigned` | `retired`
- `on_leave` → `active` | `resigned`
- `resigned` → (terminal)
- `retired` → (terminal)

### DELETE `/{teacher_code}` (admin)
Soft-delete teacher.

---

## 6. Classrooms

Base path: `/api/v1/classrooms`

### POST `/` (admin)
Create new classroom.

### GET `/` (admin)
List classrooms with filters.

**Query params:**
- `search` - Search by code or name
- `class_type` - Filter by type
- `academic_year` - Filter by year
- `grade_level` - Filter by grade (1-13)
- `homeroom_teacher_id` - Filter by homeroom teacher
- `has_capacity` - Filter by availability
- `page`, `page_size` - Pagination

### GET `/{class_code}` (admin)
Get classroom details.

### PATCH `/{class_code}` (admin)
Update classroom.

### PATCH `/{class_code}/status` (admin)
Update classroom status.

### DELETE `/{class_code}` (admin)
Soft-delete classroom.

### POST `/{class_code}/enrollments` (admin)
Enroll student in classroom.

### GET `/{class_code}/enrollments` (admin)
List enrollments in classroom.

### GET `/students/{student_id}/enrollments` (admin)
Get all enrollments for a student.

### GET `/enrollments/{enrollment_id}` (admin)
Get enrollment details.

### PATCH `/enrollments/{enrollment_id}` (admin)
Update enrollment notes.

### PATCH `/enrollments/{enrollment_id}/status` (admin)
Update enrollment status.

---

## 7. Grading

Base path: `/api/v1/grading`

### Subjects

#### POST `/subjects` (admin|teacher)
Create subject.

#### GET `/subjects` (admin|teacher)
List subjects.

#### GET `/subjects/{subject_code}` (admin|teacher)
Get subject details.

#### PATCH `/subjects/{subject_code}` (admin|teacher)
Update subject.

### Class Subjects (Assignments)

#### POST `/class-subjects` (admin|teacher)
Assign subject to class with teacher.

#### GET `/class-subjects` (admin|teacher)
List class-subject assignments.

**Query params:**
- `classroom_id`
- `teacher_id`
- `academic_year`
- `semester` (1 or 2)

#### GET `/class-subjects/{cs_id}` (admin|teacher)
Get class-subject details.

#### PATCH `/class-subjects/{cs_id}` (admin|teacher)
Update class-subject (assign/change teacher).

### Grade Components

#### POST `/grade-components` (admin|teacher)
Create grade component (midterm, final, homework...).

#### GET `/grade-components/{class_subject_id}` (admin|teacher)
List grade components for a class-subject.

#### PATCH `/grade-components/{gc_id}` (admin|teacher)
Update grade component.

### Student Grades

#### POST `/grades` (admin|teacher)
Enter grade for one student.

#### POST `/grades/bulk` (admin|teacher)
Bulk enter grades for multiple students.

#### GET `/grades/{grade_id}` (admin|teacher)
Get grade details.

#### PATCH `/grades/{grade_id}` (admin|teacher)
Update grade (requires reason - creates audit log).

#### GET `/grades/{grade_id}/audit-logs` (admin|teacher)
Get grade change history.

#### GET `/class-subjects/{cs_id}/grade-matrix` (admin|teacher)
Get full grade matrix for class-subject.

#### GET `/class-subjects/{cs_id}/grades` (admin|teacher)
List all grades in a class-subject.

### Reports & Statistics

#### GET `/students/{student_id}/report` (admin|teacher)
Get student semester report.

#### GET `/class-subjects/{cs_id}/statistics` (admin|teacher)
Get class statistics (grade distribution, averages).

---

## 8. Salary

Base path: `/api/v1/salary`

### Salary Grades

#### POST `/grades` (admin|accountant)
Create salary grade.

#### GET `/grades` (admin|accountant)
List salary grades.

#### GET `/grades/{grade_code}` (admin|accountant)
Get salary grade details.

#### PATCH `/grades/{grade_code}` (admin|accountant)
Update salary grade.

### Bonus Policies

#### POST `/bonus-policies` (admin|accountant)
Create bonus policy.

#### GET `/bonus-policies` (admin|accountant)
List bonus policies.

#### GET `/bonus-policies/{policy_code}` (admin|accountant)
Get bonus policy details.

#### PATCH `/bonus-policies/{policy_code}` (admin|accountant)
Update bonus policy.

### Payroll

#### POST `/payrolls` (admin|accountant)
Create monthly payroll.

#### GET `/payrolls` (admin|accountant)
List payrolls.

**Query params:**
- `teacher_id`
- `status` (draft, confirmed, paid)
- `month_from`, `month_to`
- `page`, `page_size`

#### GET `/payrolls/{payroll_id}` (admin|accountant)
Get payroll details.

#### PATCH `/payrolls/{payroll_id}` (admin|accountant)
Update payroll (only when not paid).

#### PATCH `/payrolls/{payroll_id}/status` (admin|accountant)
Update payroll status (draft → confirmed → paid).

#### POST `/payrolls/{payroll_id}/bonuses` (admin|accountant)
Add bonus to payroll.

---

## 9. Dashboard

Base path: `/api/v1/dashboard`

### GET `/stats` (admin)
Get dashboard statistics.

**Response:**
```json
{
  "data": {
    "total_students": 120,
    "total_teachers": 15,
    "total_classrooms": 8,
    "active_students": 110,
    "active_teachers": 13,
    "recent_students": [...],
    "recent_teachers": [...]
  }
}
```

---

## 10. Lookups

Base path: `/api/v1/lookups`

Lightweight endpoints for dropdowns/selectors.

### GET `/teachers` (admin)
List teachers for dropdown.

### GET `/classrooms` (admin)
List classrooms for dropdown.

### GET `/students` (admin)
Search students for dropdown.

### GET `/subjects` (admin)
List subjects for dropdown.

---

## 11. Teacher Portal

Base path: `/api/v1/teacher`

Teacher's personal workspace.

### GET `/dashboard` (teacher)
Teacher dashboard.

### GET `/assignments` (teacher)
List teaching assignments.

### GET `/classrooms/{classroom_id}/students` (teacher)
List students in a classroom.

### GET `/gradebook/matrix` (teacher)
Get gradebook matrix for a class-subject.

### PATCH `/gradebook/entries` (teacher)
Batch upsert gradebook entries.

### GET `/attendance/matrix` (teacher)
Get attendance matrix.

### PATCH `/attendance/entries` (teacher)
Batch update attendance.

### GET `/timetable` (teacher)
Get teacher timetable.

---

## 12. Admin (Timetable & Attendance)

Base path: `/api/v1/admin`

### GET `/timetable` (admin)
List all timetables.

### POST `/timetable` (admin)
Create timetable entry.

### PATCH `/timetable/{entry_id}` (admin)
Update timetable entry.

### DELETE `/timetable/{entry_id}` (admin)
Delete timetable entry.

### GET `/attendance/matrix` (admin)
Get attendance matrix for any classroom.

### PATCH `/attendance/entries` (admin)
Batch update attendance (admin override).

---

## Response Format

### Success
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Operation description",
  "data": { ... },
  "errors": null
}
```

### Created (201)
```json
{
  "code": 201,
  "message": "Created",
  "detail": "Resource created",
  "data": { ... },
  "errors": null
}
```

### Error (4xx, 5xx)
```json
{
  "code": 400,
  "message": "Error",
  "detail": "Error description",
  "data": null,
  "errors": [...]
}
```
