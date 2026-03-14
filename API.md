# EMS Backend â€“ API Reference

> Base URL: `http://localhost:8000/api/v1`  
> Táº¥t cáº£ response Ä‘á»u bá»c trong envelope `APIResponse`:
> ```json
> { "code": 200, "message": "OK", "detail": "...", "data": { ... }, "errors": null }
> ```

**Auth & RBAC**
- Header cho endpoint báº£o vá»‡: `Authorization: Bearer <access_token>`
- Role access:
- `admin`: Dashboard, Students, Teachers, Classrooms
- `admin | teacher`: Grading
- `admin | accountant`: Salary
- `teacher`: Teacher Portal (`/api/v1/teacher/*`)
- `admin`: Admin Timetable/Attendance (`/api/v1/admin/*`)
- `admin`: Lookups (`/api/v1/lookups/*`)

---

## Má»¥c lá»¥c

1. [System](#1-system)
2. [Dashboard](#2-dashboard)
3. [Students](#3-students)
4. [Teachers](#4-teachers)
5. [Classrooms](#5-classrooms)
6. [Enrollments](#6-enrollments-lá»“ng-trong-classrooms)
7. [Grading â€“ Subjects](#7-grading--subjects)
8. [Grading â€“ Class Subjects](#8-grading--class-subjects-phÃ¢n-cÃ´ng)
9. [Grading â€“ Grade Components](#9-grading--grade-components)
10. [Grading â€“ Student Grades](#10-grading--student-grades)
11. [Grading â€“ Reports & Statistics](#11-grading--reports--statistics)
12. [Salary â€“ Salary Grades](#12-salary--salary-grades)
13. [Salary â€“ Bonus Policies](#13-salary--bonus-policies)
14. [Salary â€“ Payrolls](#14-salary--payrolls)
15. [Enums Reference](#15-enums-reference)
16. [Business Logic & Luá»“ng xá»­ lÃ½](#16-business-logic--luá»“ng-xá»­-lÃ½)
17. [Teacher Portal (Phase 1)](#17-teacher-portal-phase-1)
18. [Auth](#18-auth)
19. [Admin Timetable & Attendance](#19-admin-timetable--attendance)
20. [Lookups](#20-lookups)

---

## 1. System

| Method | Path | MÃ´ táº£ |
|--------|------|-------|
| GET | `/health` | Health check |

---

## 2. Dashboard

### GET `/dashboard/stats`
Thá»‘ng kÃª tá»•ng quan há»‡ thá»‘ng.

**Response data:**
```json
{
  "total_students": 120,
  "total_teachers": 15,
  "total_classrooms": 8,
  "active_students": 110,
  "active_teachers": 13,
  "recent_students": [ ...5 há»c sinh má»›i nháº¥t... ],
  "recent_teachers": [ ...5 giÃ¡o viÃªn má»›i nháº¥t... ]
}
```

---

## 3. Students

### POST `/students`
Táº¡o há»c sinh má»›i.

**Body (required: `*`):**
```json
{
  "student_code": "SV2024001",       // * unique, max 20 kÃ½ tá»±
  "full_name": "Nguyen Van An",      // * max 150 kÃ½ tá»±
  "date_of_birth": "2006-05-15",     // optional, YYYY-MM-DD
  "gender": "male",                  // optional: "male" | "female" | "other"
  "national_id": "012345678901",     // optional, unique, max 20
  "email": "an@student.edu.vn",      // optional, unique
  "phone_number": "0901234567",      // optional, max 20
  "address": "...",                  // optional
  "enrollment_date": "2024-09-01",   // optional, YYYY-MM-DD
  "academic_status": "active",       // optional, default: "active"
  "class_name": "12A1",              // optional, max 50
  "program_name": "CNTT",            // optional, max 200
  "parent_full_name": "...",         // optional, max 150
  "parent_phone": "0912345678",      // optional, max 20
  "parent_email": "...",             // optional
  "medical_notes": "..."             // optional
}
```

---

### GET `/students`
Danh sÃ¡ch há»c sinh (phÃ¢n trang + lá»c).

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `search` | string | TÃ¬m theo `student_code`, `full_name`, `email` |
| `academic_status` | enum | `active` \| `preserved` \| `suspended` \| `graduated` |
| `class_name` | string | Lá»c theo lá»›p |
| `program_name` | string | Lá»c theo chÆ°Æ¡ng trÃ¬nh |
| `page` | int â‰¥ 1 | Máº·c Ä‘á»‹nh: 1 |
| `page_size` | int 1â€“100 | Máº·c Ä‘á»‹nh: 20 |

---

### GET `/students/{student_code}`
Chi tiáº¿t 1 há»c sinh theo mÃ£.

---

### PATCH `/students/{student_code}`
Cáº­p nháº­t thÃ´ng tin há»c sinh (partial update â€“ chá»‰ gá»­i fields cáº§n sá»­a).

**Body:** Táº¥t cáº£ fields Ä‘á»u optional (giá»‘ng Create nhÆ°ng khÃ´ng cÃ³ `student_code`):
```json
{
  "phone_number": "0909999888",
  "address": "123 Nguyen Hue, Q1",
  "class_name": "12A2",
  "enrollment_date": "2024-09-01"
}
```

---

### PATCH `/students/{student_code}/status`
Thay Ä‘á»•i tráº¡ng thÃ¡i há»c vá»¥.

**Body:**
```json
{
  "new_status": "preserved",   // * enum StudentStatus
  "reason": "Nghá»‰ há»c vÃ¬ lÃ½ do cÃ¡ nhÃ¢n"  // optional
}
```

**Luá»“ng chuyá»ƒn tráº¡ng thÃ¡i há»£p lá»‡:**
```
active â†’ preserved | suspended | graduated
preserved â†’ active | suspended
suspended â†’ active
graduated â†’ (terminal â€“ khÃ´ng thá»ƒ chuyá»ƒn)
```

---

### DELETE `/students/{student_code}`
Soft-delete há»c sinh (`is_active = false`). Dá»¯ liá»‡u váº«n giá»¯ láº¡i trong DB.

---

## 4. Teachers

### POST `/teachers`
Táº¡o giÃ¡o viÃªn má»›i.

**Body (required: `*`):**
```json
{
  "teacher_code": "GV2024001",       // * unique, max 20
  "full_name": "Tran Thi Mai",       // * max 150
  "date_of_birth": "1985-03-20",     // optional
  "gender": "female",                // optional: "male" | "female" | "other"
  "national_id": "...",              // optional, unique, max 20
  "email": "mai@school.edu.vn",      // optional, unique
  "phone_number": "0987654321",      // optional, max 20
  "address": "...",                  // optional
  "join_date": "2024-09-01",         // optional
  "employment_status": "active",     // optional, default: "active"
  "specialization": "ToÃ¡n há»c",      // optional, max 200
  "qualification": "Tháº¡c sÄ©",        // optional, max 200
  "department": "Khoa há»c tá»± nhiÃªn"  // optional, max 200
}
```

---

### GET `/teachers`
Danh sÃ¡ch giÃ¡o viÃªn (phÃ¢n trang + lá»c).

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `search` | string | TÃ¬m theo `teacher_code`, `full_name`, `email` |
| `employment_status` | enum | `active` \| `on_leave` \| `resigned` \| `retired` |
| `department` | string | Lá»c theo phÃ²ng ban |
| `specialization` | string | Lá»c theo chuyÃªn mÃ´n |
| `page` | int â‰¥ 1 | Máº·c Ä‘á»‹nh: 1 |
| `page_size` | int 1â€“100 | Máº·c Ä‘á»‹nh: 20 |

---

### GET `/teachers/{teacher_code}`
Chi tiáº¿t 1 giÃ¡o viÃªn.

---

### PATCH `/teachers/{teacher_code}`
Cáº­p nháº­t thÃ´ng tin giÃ¡o viÃªn (partial update).

**Body:** Táº¥t cáº£ fields optional (khÃ´ng cÃ³ `teacher_code`):
```json
{
  "phone_number": "0909999888",
  "department": "Khoa há»c xÃ£ há»™i",
  "join_date": "2024-01-01"
}
```

---

### PATCH `/teachers/{teacher_code}/status`
Thay Ä‘á»•i tráº¡ng thÃ¡i cÃ´ng tÃ¡c.

**Body:**
```json
{
  "new_status": "on_leave",        // * enum TeacherStatus
  "reason": "Nghá»‰ thai sáº£n 6 thÃ¡ng"  // optional
}
```

**Luá»“ng chuyá»ƒn tráº¡ng thÃ¡i há»£p lá»‡:**
```
active â†’ on_leave | resigned | retired
on_leave â†’ active | resigned
resigned â†’ (terminal)
retired â†’ (terminal)
```

---

### DELETE `/teachers/{teacher_code}`
Soft-delete giÃ¡o viÃªn.

---

## 5. Classrooms

### POST `/classrooms`
Táº¡o lá»›p há»c má»›i.

**Body (required: `*`):**
```json
{
  "class_code": "10A1-2024",         // * unique, max 30
  "class_name": "Lá»›p 10A1",          // * max 100
  "class_type": "standard",          // optional, default: "standard"
  "academic_year": "2024-2025",      // * format "YYYY-YYYY"
  "grade_level": 10,                 // * integer 1â€“13
  "max_capacity": 40,                // optional, default: 40 (1â€“200)
  "homeroom_teacher_id": 3,          // optional, FK â†’ teachers.id
  "room_number": "P.201",            // optional, max 20
  "description": "..."               // optional, max 300
}
```

> **Logic:** `class_code` pháº£i unique. Há»‡ thá»‘ng tá»± track `current_enrollment` (khÃ´ng nháº­p tay).

---

### GET `/classrooms`
Danh sÃ¡ch lá»›p há»c (phÃ¢n trang + lá»c).

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `search` | string | TÃ¬m theo `class_code` hoáº·c `class_name` |
| `class_type` | enum | `standard` \| `specialized` \| `advanced` |
| `academic_year` | string | VD: `"2024-2025"` |
| `grade_level` | int 1â€“13 | Khá»‘i lá»›p |
| `homeroom_teacher_id` | int | ID giÃ¡o viÃªn chá»§ nhiá»‡m |
| `page` | int â‰¥ 1 | Máº·c Ä‘á»‹nh: 1 |
| `page_size` | int 1â€“100 | Máº·c Ä‘á»‹nh: 20 |

---

### GET `/classrooms/{class_code}`
Chi tiáº¿t 1 lá»›p há»c.

---

### PATCH `/classrooms/{class_code}`
Cáº­p nháº­t thÃ´ng tin lá»›p há»c.

**Body:** Táº¥t cáº£ fields optional:
```json
{
  "room_number": "P.305",
  "max_capacity": 35,
  "homeroom_teacher_id": 3,
  "description": "..."
}
```

---

### PATCH `/classrooms/{class_code}/status`
Cáº­p nháº­t tráº¡ng thÃ¡i lÃ³p (active / inactive).

**Body:**
```json
{ "is_active": false }
```

*Ghi chú:* có thể gửi `new_status` = `"active"` | `"inactive"`.

---

### DELETE `/classrooms/{class_code}`
Soft-delete lá»›p há»c.

---

## 6. Enrollments (lá»“ng trong Classrooms)

### POST `/classrooms/{class_code}/enrollments`
ÄÄƒng kÃ½ há»c sinh vÃ o lá»›p.

**Path:** `class_code` â€“ mÃ£ lá»›p (string).

**Body (required: `*`):**
```json
{
  "student_id": 1,                   // * FK â†’ students.id
  "classroom_id": 2,                 // * FK â†’ classrooms.id (sáº½ bá»‹ override bá»Ÿi path param)
  "enrollment_type": "primary",      // optional, default: "primary"
  "enrolled_date": "2024-09-01",     // optional
  "notes": "Chuyá»ƒn Ä‘áº¿n tá»« trÆ°á»ng khÃ¡c"  // optional, max 300
}
```

> **Logic nghiá»‡p vá»¥:**
> 1. Kiá»ƒm tra lá»›p tá»“n táº¡i (theo `class_code`).
> 2. Kiá»ƒm tra `current_enrollment < max_capacity` â†’ náº¿u Ä‘áº§y: `ClassroomCapacityExceeded`.
> 3. Náº¿u `enrollment_type = "primary"`: kiá»ƒm tra há»c sinh chÆ°a cÃ³ lá»›p chÃ­nh nÃ o Ä‘ang active â†’ náº¿u cÃ³: `DuplicatePrimaryEnrollment`.
> 4. Kiá»ƒm tra khÃ´ng trÃ¹ng láº·p cÃ¹ng loáº¡i enrollment trong cÃ¹ng lá»›p â†’ `EnrollmentAlreadyExists`.

---

### GET `/classrooms/{class_code}/enrollments`
Danh sÃ¡ch há»c sinh trong lá»›p.

**Path:** `class_code` â€“ mÃ£ lá»›p.

**Query params:**
| Param | Type | Máº·c Ä‘á»‹nh |
|-------|------|---------|
| `page` | int â‰¥ 1 | 1 |
| `page_size` | int 1â€“200 | 50 |

---

### GET `/classrooms/enrollments/{enrollment_id}`
Chi tiáº¿t 1 báº£n ghi enrollment.

---

### PATCH `/classrooms/enrollments/{enrollment_id}`
Cáº­p nháº­t ghi chÃº enrollment.

**Body:**
```json
{
  "notes": "Há»c sinh chuyá»ƒn Ä‘áº¿n tá»« trÆ°á»ng khÃ¡c"  // optional, max 300
}
```

---

### PATCH `/classrooms/enrollments/{enrollment_id}/status`
Thay Ä‘á»•i tráº¡ng thÃ¡i enrollment.

**Body:**
```json
{
  "new_status": "transferred",       // * enum EnrollmentStatus
  "left_date": "2024-12-01",         // optional
  "notes": "Chuyá»ƒn sang lá»›p 10A2"    // optional, max 300
}
```

**Luá»“ng chuyá»ƒn tráº¡ng thÃ¡i há»£p lá»‡:**
```
active â†’ transferred | withdrawn | completed
transferred â†’ (terminal)
withdrawn â†’ (terminal)
completed â†’ (terminal)
```

---

### GET `/classrooms/students/{student_id}/enrollments`
Táº¥t cáº£ lá»›p mÃ  1 há»c sinh Ä‘ang/Ä‘Ã£ tham gia.

---

## 7. Grading â€“ Subjects

### POST `/grading/subjects`
Táº¡o mÃ´n há»c.

**Body (required: `*`):**
```json
{
  "subject_code": "TOAN",            // * unique, max 20
  "subject_name": "ToÃ¡n há»c",        // * max 100
  "subject_type": "standard",        // optional, default: "standard"
  "credits": 4,                      // optional, default: 1 (1â€“10)
  "description": "..."               // optional, max 300
}
```

---

### GET `/grading/subjects`
Danh sÃ¡ch mÃ´n há»c.

**Query params:**
| Param | Type | Máº·c Ä‘á»‹nh |
|-------|------|---------|
| `page` | int â‰¥ 1 | 1 |
| `page_size` | int 1â€“100 | 20 |
| `active_only` | bool | `true` |

---

### GET `/grading/subjects/{subject_code}`
Chi tiáº¿t mÃ´n há»c.

---

### PATCH `/grading/subjects/{subject_code}`
Cáº­p nháº­t mÃ´n há»c.

**Body:** Táº¥t cáº£ optional:
```json
{
  "subject_name": "ToÃ¡n cao cáº¥p",
  "credits": 5,
  "description": "...",
  "is_active": true
}
```

---

## 8. Grading â€“ Class Subjects (PhÃ¢n cÃ´ng)

> **Class Subject** = MÃ´n há»c Ä‘Æ°á»£c phÃ¢n cÃ´ng dáº¡y táº¡i 1 lá»›p, 1 há»c ká»³, bá»Ÿi 1 giÃ¡o viÃªn.  
> ÄÃ¢y lÃ  Ä‘Æ¡n vá»‹ gá»‘c Ä‘á»ƒ nháº­p Ä‘iá»ƒm.

### POST `/grading/class-subjects`
PhÃ¢n cÃ´ng mÃ´n há»c cho lá»›p + giÃ¡o viÃªn.

**Body (required: `*`):**
```json
{
  "classroom_id": 1,                 // * FK â†’ classrooms.id
  "subject_id": 2,                   // * FK â†’ subjects.id
  "teacher_id": 3,                   // optional, FK â†’ teachers.id
  "semester": 1,                     // * 1 hoáº·c 2
  "academic_year": "2024-2025"       // * format "YYYY-YYYY"
}
```

> **Logic:** KhÃ´ng Ä‘Æ°á»£c táº¡o trÃ¹ng `(classroom_id, subject_id, semester, academic_year)`.

---

### GET `/grading/class-subjects`
Danh sÃ¡ch phÃ¢n cÃ´ng mÃ´n.

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `classroom_id` | int | Lá»c theo lá»›p |
| `teacher_id` | int | Lá»c theo giÃ¡o viÃªn |
| `academic_year` | string | VD: `"2024-2025"` |
| `semester` | int 1â€“2 | Há»c ká»³ |
| `page` | int â‰¥ 1 | Máº·c Ä‘á»‹nh: 1 |
| `page_size` | int 1â€“200 | Máº·c Ä‘á»‹nh: 50 |

---

### GET `/grading/class-subjects/{cs_id}`
Chi tiáº¿t phÃ¢n cÃ´ng mÃ´n.

---

### PATCH `/grading/class-subjects/{cs_id}`
Cáº­p nháº­t phÃ¢n cÃ´ng (Ä‘á»•i/gÃ¡n giÃ¡o viÃªn, báº­t/táº¯t).

**Body:**
```json
{
  "teacher_id": 5,     // optional
  "is_active": true    // optional
}
```

---

## 9. Grading â€“ Grade Components

> **Grade Component** = ThÃ nh pháº§n Ä‘iá»ƒm (miá»‡ng, 15 phÃºt, 1 tiáº¿t, há»c ká»³â€¦) cá»§a 1 Class Subject.  
> Má»—i component cÃ³ trá»ng sá»‘ (`weight_percent`). Tá»•ng weight cá»§a cÃ¡c component trong 1 class-subject nÃªn = 100%.

### POST `/grading/grade-components`
Táº¡o thÃ nh pháº§n Ä‘iá»ƒm.

**Body (required: `*`):**
```json
{
  "class_subject_id": 1,             // * FK â†’ class_subjects.id
  "component_name": "Kiá»ƒm tra miá»‡ng", // * max 100
  "weight_percent": 10,              // * 1â€“100 (%)
  "min_count": 2                     // optional, default: 1 â€“ sá»‘ bÃ i tá»‘i thiá»ƒu
}
```

---

### GET `/grading/grade-components/{class_subject_id}`
Danh sÃ¡ch thÃ nh pháº§n Ä‘iá»ƒm cá»§a 1 class-subject.

---

### PATCH `/grading/grade-components/{gc_id}`
Cáº­p nháº­t thÃ nh pháº§n Ä‘iá»ƒm.

**Body:** Táº¥t cáº£ optional:
```json
{
  "component_name": "Kiá»ƒm tra 15 phÃºt",
  "weight_percent": 15,
  "min_count": 3,
  "is_active": true
}
```

---

## 10. Grading â€“ Student Grades

> **Äiá»u kiá»‡n trÆ°á»›c:** Pháº£i cÃ³ `class_subject_id` vÃ  `grade_component_id` tÆ°Æ¡ng á»©ng.

### POST `/grading/grades`
Nháº­p Ä‘iá»ƒm cho 1 há»c sinh.

**Body (required: `*`):**
```json
{
  "student_id": 1,                   // * FK â†’ students.id
  "class_subject_id": 3,             // * FK â†’ class_subjects.id
  "grade_component_id": 2,           // * FK â†’ grade_components.id
  "score": 8.5,                      // * 0â€“10 (decimal)
  "exam_date": "2024-11-10",         // optional
  "entered_by": 4                    // optional â€“ ID giÃ¡o viÃªn nháº­p Ä‘iá»ƒm
}
```

> **Logic:** KhÃ´ng cho phÃ©p nháº­p trÃ¹ng `(student_id, class_subject_id, grade_component_id)`.

---

### POST `/grading/grades/bulk`
Nháº­p Ä‘iá»ƒm hÃ ng loáº¡t (nhiá»u há»c sinh, cÃ¹ng 1 cá»™t Ä‘iá»ƒm).

**Body (required: `*`):**
```json
{
  "class_subject_id": 3,             // *
  "grade_component_id": 2,           // *
  "exam_date": "2024-11-10",         // optional
  "entered_by": 4,                   // optional
  "grades": [                        // * danh sÃ¡ch Ä‘iá»ƒm
    { "student_id": 1, "score": 8.5 },
    { "student_id": 2, "score": 7.0 },
    { "student_id": 3, "score": 9.0 }
  ]
}
```

---

### GET `/grading/grades/{grade_id}`
Chi tiáº¿t 1 báº£n ghi Ä‘iá»ƒm.

---

### PATCH `/grading/grades/{grade_id}`
Sá»­a Ä‘iá»ƒm (báº¯t buá»™c cÃ³ lÃ½ do â€“ ghi audit log tá»± Ä‘á»™ng).

**Body (required: `*`):**
```json
{
  "score": 9.0,                      // * 0â€“10
  "reason": "Cháº¥m sai, Ä‘Ã£ phÃºc tra láº¡i",  // * báº¯t buá»™c, max 300
  "modified_by": 4                   // optional â€“ ID giÃ¡o viÃªn sá»­a
}
```

> **Logic:** Má»—i láº§n sá»­a táº¡o 1 báº£n ghi `GradeAuditLog` lÆ°u Ä‘iá»ƒm cÅ©, Ä‘iá»ƒm má»›i, lÃ½ do.

---

### GET `/grading/grades/{grade_id}/audit-logs`
Lá»‹ch sá»­ thay Ä‘á»•i Ä‘iá»ƒm cá»§a 1 báº£n ghi.

---

### GET `/grading/class-subjects/{cs_id}/grades`
Táº¥t cáº£ Ä‘iá»ƒm trong 1 class-subject.

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `grade_component_id` | int | Lá»c theo cá»™t Ä‘iá»ƒm |
| `page` | int â‰¥ 1 | Máº·c Ä‘á»‹nh: 1 |
| `page_size` | int 1â€“500 | Máº·c Ä‘á»‹nh: 100 |

---

## 11. Grading â€“ Reports & Statistics

### GET `/grading/students/{student_id}/report`
BÃ¡o cÃ¡o Ä‘iá»ƒm há»c sinh theo há»c ká»³.

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `semester` | int 1â€“2 | Lá»c theo há»c ká»³ |
| `academic_year` | string | VD: `"2024-2025"` |

**Response data:**
```json
{
  "student_id": 1,
  "semester": 1,
  "academic_year": "2024-2025",
  "subjects": [ ...SemesterAverageResponse... ],
  "overall_average": 8.2,
  "overall_rank": "Gioi"
}
```

---

### GET `/grading/class-subjects/{cs_id}/statistics`
Thá»‘ng kÃª Ä‘iá»ƒm cá»§a cáº£ lá»›p cho 1 mÃ´n há»c.

**Response data:**
```json
{
  "class_subject_id": 3,
  "classroom_id": 1,
  "subject_id": 2,
  "semester": 1,
  "academic_year": "2024-2025",
  "total_students": 40,
  "avg_score": 7.5,
  "max_score": 10.0,
  "min_score": 3.5,
  "rank_distribution": {
    "Gioi": 10,
    "Kha": 15,
    "TrungBinh": 12,
    "Yeu": 3
  }
}
```

---

## 12. Salary â€“ Salary Grades

> **Salary Grade** = Ngáº¡ch lÆ°Æ¡ng, Ä‘á»‹nh nghÄ©a má»©c lÆ°Æ¡ng cÆ¡ báº£n vÃ  Ä‘Æ¡n giÃ¡ tiáº¿t dáº¡y theo trÃ¬nh Ä‘á»™ + thÃ¢m niÃªn.

### POST `/salary/grades`
Táº¡o ngáº¡ch lÆ°Æ¡ng.

**Body (required: `*`):**
```json
{
  "grade_code": "THAC_SI_3_6NAM",    // * unique, max 30
  "qualification_level": "thac_si",  // * enum QualificationLevel
  "experience_tier": "3_to_6y",      // * enum ExperienceTier
  "base_salary": 8500000,            // * VNÄ/thÃ¡ng, â‰¥ 0
  "hourly_rate": 85000,              // * VNÄ/tiáº¿t, â‰¥ 0
  "effective_from": "2024-01-01",    // * YYYY-MM-DD
  "effective_to": null,              // optional
  "description": "..."               // optional, max 300
}
```

---

### GET `/salary/grades`
Danh sÃ¡ch ngáº¡ch lÆ°Æ¡ng.

**Query params:** `page`, `page_size`, `active_only` (default: `true`).

---

### GET `/salary/grades/{grade_code}`
Chi tiáº¿t ngáº¡ch lÆ°Æ¡ng.

---

### PATCH `/salary/grades/{grade_code}`
Cáº­p nháº­t ngáº¡ch lÆ°Æ¡ng.

**Body:** Táº¥t cáº£ optional:
```json
{
  "base_salary": 9000000,
  "hourly_rate": 90000,
  "effective_to": "2025-12-31",
  "description": "...",
  "is_active": false
}
```

---

## 13. Salary â€“ Bonus Policies

> **Bonus Policy** = ChÃ­nh sÃ¡ch thÆ°á»Ÿng tÃ¡i sá»­ dá»¥ng (thÆ°á»Ÿng thÃ¢m niÃªn, thÆ°á»Ÿng GVCN...).

### POST `/salary/bonus-policies`
Táº¡o chÃ­nh sÃ¡ch thÆ°á»Ÿng.

**Body (required: `*`):**
```json
{
  "policy_code": "THUONG_THAM_NIEN_3NAM",     // * unique, max 30
  "policy_name": "ThÆ°á»Ÿng Ä‘áº¡t má»‘c 3 nÄƒm",      // * max 200
  "bonus_type": "fixed",                        // optional, default: "fixed"
  "bonus_value": 500000,                        // * â‰¥ 0
  "condition_description": "..."               // optional, max 500
}
```

---

### GET `/salary/bonus-policies`
Danh sÃ¡ch chÃ­nh sÃ¡ch thÆ°á»Ÿng.

**Query params:** `page`, `page_size`, `active_only` (default: `true`).

---

### GET `/salary/bonus-policies/{policy_code}`
Chi tiáº¿t chÃ­nh sÃ¡ch thÆ°á»Ÿng.

---

### PATCH `/salary/bonus-policies/{policy_code}`
Cáº­p nháº­t chÃ­nh sÃ¡ch thÆ°á»Ÿng.

**Body:** Táº¥t cáº£ optional:
```json
{
  "policy_name": "...",
  "bonus_type": "percentage",
  "bonus_value": 10,
  "condition_description": "...",
  "is_active": true
}
```

---

## 14. Salary â€“ Payrolls

> **Payroll** = Báº£ng lÆ°Æ¡ng thÃ¡ng cá»§a 1 giÃ¡o viÃªn. Tráº£i qua 3 tráº¡ng thÃ¡i: `draft â†’ confirmed â†’ paid`.

### POST `/salary/payrolls`
Táº¡o báº£ng lÆ°Æ¡ng thÃ¡ng.

**Body (required: `*`):**
```json
{
  "teacher_id": 1,                   // * FK â†’ teachers.id
  "salary_grade_id": 2,              // * FK â†’ salary_grades.id
  "payroll_month": "2024-09-01",     // * lÆ°u ngÃ y 1 cá»§a thÃ¡ng, YYYY-MM-DD
  "work_days_standard": 22,          // optional, default: 22
  "work_days_actual": 21,            // optional, default: 0
  "teaching_hours_standard": 80,     // optional, default: 0
  "teaching_hours_actual": 90,       // optional, default: 0
  "base_salary": 8500000,            // optional, default: 0
  "teaching_allowance": 850000,      // optional, default: 0
  "deductions": 0,                   // optional, default: 0
  "notes": "...",                    // optional, max 500
  "bonus_details": [                 // optional, danh sÃ¡ch khoáº£n thÆ°á»Ÿng Ä‘Ã­nh kÃ¨m
    {
      "bonus_policy_id": 1,          // * FK â†’ bonus_policies.id
      "amount": 500000,              // * â‰¥ 0
      "note": "ThÆ°á»Ÿng thÃ¢m niÃªn"     // optional, max 300
    }
  ]
}
```

> **Logic:** `net_salary = base_salary + teaching_allowance + total_bonus - deductions`. Tá»± tÃ­nh khi táº¡o/cáº­p nháº­t.

---

### GET `/salary/payrolls`
Danh sÃ¡ch báº£ng lÆ°Æ¡ng (cÃ³ lá»c).

**Query params:**
| Param | Type | MÃ´ táº£ |
|-------|------|-------|
| `teacher_id` | int | Lá»c theo giÃ¡o viÃªn |
| `status` | enum | `draft` \| `confirmed` \| `paid` |
| `month_from` | YYYY-MM-DD | Lá»c tá»« thÃ¡ng |
| `month_to` | YYYY-MM-DD | Lá»c Ä‘áº¿n thÃ¡ng |
| `page` | int â‰¥ 1 | Máº·c Ä‘á»‹nh: 1 |
| `page_size` | int 1â€“100 | Máº·c Ä‘á»‹nh: 20 |

---

### GET `/salary/payrolls/{payroll_id}`
Chi tiáº¿t báº£ng lÆ°Æ¡ng (bao gá»“m danh sÃ¡ch `bonus_details`).

---

### PATCH `/salary/payrolls/{payroll_id}`
Cáº­p nháº­t báº£ng lÆ°Æ¡ng (chá»‰ cho phÃ©p khi status = `draft`).

**Body:** Táº¥t cáº£ optional:
```json
{
  "work_days_actual": 20,
  "teaching_hours_actual": 85,
  "teaching_allowance": 800000,
  "deductions": 100000,
  "notes": "..."
}
```

---

### PATCH `/salary/payrolls/{payroll_id}/status`
Duyá»‡t / thanh toÃ¡n báº£ng lÆ°Æ¡ng.

**Body:**
```json
{
  "new_status": "confirmed",         // * enum PayrollStatus
  "confirmed_by": 5,                 // optional â€“ ID ngÆ°á»i duyá»‡t
  "notes": "ÄÃ£ kiá»ƒm tra, duyá»‡t chi"  // optional, max 500
}
```

**Luá»“ng chuyá»ƒn tráº¡ng thÃ¡i há»£p lá»‡:**
```
draft â†’ confirmed
confirmed â†’ paid
paid â†’ (terminal)
```

---

### POST `/salary/payrolls/{payroll_id}/bonuses`
ThÃªm khoáº£n thÆ°á»Ÿng vÃ o báº£ng lÆ°Æ¡ng (chá»‰ khi chÆ°a `paid`).

**Body:**
```json
{
  "bonus_policy_id": 1,              // * FK â†’ bonus_policies.id
  "amount": 500000,                  // * â‰¥ 0
  "note": "ThÆ°á»Ÿng GVCN"             // optional, max 300
}
```

> **Logic:** Sau khi thÃªm bonus, `total_bonus` vÃ  `net_salary` Ä‘Æ°á»£c tÃ­nh láº¡i tá»± Ä‘á»™ng.

---

## 15. Enums Reference

### StudentStatus
| Value | Ã nghÄ©a |
|-------|---------|
| `active` | Äang há»c |
| `preserved` | Báº£o lÆ°u |
| `suspended` | ÄÃ¬nh chá»‰ |
| `graduated` | ÄÃ£ tá»‘t nghiá»‡p |

### TeacherStatus
| Value | Ã nghÄ©a |
|-------|---------|
| `active` | Äang cÃ´ng tÃ¡c |
| `on_leave` | Äang nghá»‰ phÃ©p |
| `resigned` | ÄÃ£ nghá»‰ viá»‡c |
| `retired` | ÄÃ£ vá» hÆ°u |

### ClassType
| Value | Ã nghÄ©a |
|-------|---------|
| `standard` | Lá»›p thÆ°á»ng |
| `specialized` | Lá»›p chuyÃªn |
| `advanced` | Lá»›p nÃ¢ng cao |

### EnrollmentType
| Value | Ã nghÄ©a |
|-------|---------|
| `primary` | Lá»›p chÃ­nh (má»—i HS chá»‰ cÃ³ 1) |
| `secondary` | Lá»›p phá»¥ / cÃ¢u láº¡c bá»™ |

### EnrollmentStatus
| Value | Ã nghÄ©a |
|-------|---------|
| `active` | Äang há»c |
| `transferred` | ÄÃ£ chuyá»ƒn lá»›p |
| `withdrawn` | ÄÃ£ rÃºt khá»i lá»›p |
| `completed` | HoÃ n thÃ nh |

### SubjectType
| Value | Ã nghÄ©a |
|-------|---------|
| `standard` | MÃ´n báº¯t buá»™c |
| `elective` | MÃ´n tá»± chá»n |
| `extra` | MÃ´n ngoáº¡i khÃ³a |

### AcademicRank (xáº¿p loáº¡i)
| Value | Äiá»ƒm TB |
|-------|---------|
| `Gioi` | â‰¥ 8.0 |
| `Kha` | 6.5â€“7.9 |
| `TrungBinh` | 5.0â€“6.4 |
| `Yeu` | < 5.0 |

### QualificationLevel
`dai_hoc` \| `thac_si` \| `tien_si` \| `giao_su`

### ExperienceTier
`under_3y` \| `3_to_6y` \| `6_to_10y` \| `over_10y`

### BonusType
`fixed` \| `percentage`

### PayrollStatus
`draft` \| `confirmed` \| `paid`

---

## 16. Business Logic & Luá»“ng xá»­ lÃ½

### Luá»“ng hoÃ n chá»‰nh: Nháº­p Ä‘iá»ƒm cho 1 lá»›p

```
1. Táº¡o Teacher          POST /teachers
2. Táº¡o Classroom        POST /classrooms
3. Enroll Students      POST /classrooms/{class_code}/enrollments  (má»—i HS)
4. Táº¡o Subject          POST /grading/subjects
5. PhÃ¢n cÃ´ng dáº¡y        POST /grading/class-subjects
      â””â”€ classroom_id + subject_id + teacher_id + semester + academic_year
6. Cáº¥u hÃ¬nh thÃ nh pháº§n Ä‘iá»ƒm
                        POST /grading/grade-components  (má»—i cá»™t: miá»‡ng, 15p, 1tiáº¿t, HK...)
7. Nháº­p Ä‘iá»ƒm            POST /grading/grades  hoáº·c  POST /grading/grades/bulk
8. Xem bÃ¡o cÃ¡o há»c sinh GET /grading/students/{student_id}/report
9. Xem thá»‘ng kÃª lá»›p     GET /grading/class-subjects/{cs_id}/statistics
```

### Luá»“ng hoÃ n chá»‰nh: Xá»­ lÃ½ lÆ°Æ¡ng giÃ¡o viÃªn

```
1. Táº¡o SalaryGrade      POST /salary/grades
      â””â”€ qualification_level + experience_tier + base_salary + hourly_rate
2. Táº¡o BonusPolicy      POST /salary/bonus-policies  (náº¿u cÃ³ thÆ°á»Ÿng)
3. Táº¡o Payroll thÃ¡ng    POST /salary/payrolls
      â””â”€ teacher_id + salary_grade_id + payroll_month + giá» dáº¡y + kháº¥u trá»« + bonus
4. Duyá»‡t payroll        PATCH /salary/payrolls/{id}/status  { "new_status": "confirmed" }
5. Thanh toÃ¡n           PATCH /salary/payrolls/{id}/status  { "new_status": "paid" }
```

### RÃ ng buá»™c quan trá»ng

| RÃ ng buá»™c | MÃ´ táº£ |
|-----------|-------|
| `student_code`, `teacher_code`, `class_code`, `subject_code` | Unique trong toÃ n há»‡ thá»‘ng |
| `email`, `national_id` (student/teacher) | Unique náº¿u cÃ³ giÃ¡ trá»‹ |
| Enrollment PRIMARY | Má»—i há»c sinh chá»‰ Ä‘Æ°á»£c cÃ³ 1 lá»›p primary active táº¡i 1 thá»i Ä‘iá»ƒm |
| Enrollment capacity | KhÃ´ng thá»ƒ enroll khi `current_enrollment >= max_capacity` |
| Grade unique | `(student_id, class_subject_id, grade_component_id)` unique |
| Grade audit | Má»i thao tÃ¡c sá»­a Ä‘iá»ƒm Ä‘á»u báº¯t buá»™c `reason` vÃ  táº¡o audit log |
| Payroll editable | Chá»‰ cáº­p nháº­t/thÃªm bonus khi `status != paid` |
| Status transition | Má»i chuyá»ƒn tráº¡ng thÃ¡i Ä‘á»u cÃ³ whitelist há»£p lá»‡, vi pháº¡m tráº£ lá»—i |
| Soft-delete | KhÃ´ng xÃ³a cá»©ng báº¥t ká»³ record nÃ o â€“ chá»‰ set `is_active = false` |


---

## 17. Teacher Portal (Phase 1)

**Auth:** Các endpoint dưới đây yêu cầu header `Authorization: Bearer <token>` và role `teacher`. 

> Namespace: `/api/v1/teacher/*`
>

### GET `/teacher/dashboard`
Tổng quan cho giáo viên.

**Response data:**
```json
{
  "assignments_count": 4,
  "classrooms_count": 3,
  "subjects_count": 2,
  "upcoming_lessons": [
    {
      "id": 9001,
      "start": "2026-03-11T08:00:00",
      "end": "2026-03-11T09:30:00",
      "class_name": "Lớp 10A1",
      "subject_name": "Toán",
      "room_number": "A-302"
    }
  ]
}
```

---

### GET `/teacher/assignments`
Danh sách lớp-môn giáo viên phụ trách.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `academic_year` | string | VD: `2025-2026` |
| `semester` | int | 1 hoặc 2 |

**Response data:**
```json
{
  "items": [
    {
      "class_subject_id": 501,
      "classroom_id": 18,
      "class_code": "10A1-2025",
      "class_name": "Lớp 10A1",
      "subject_id": 7,
      "subject_code": "TOAN",
      "subject_name": "Toán",
      "semester": 2,
      "academic_year": "2025-2026",
      "student_count": 34
    }
  ]
}
```

---

### GET `/teacher/classrooms/{classroom_id}/students`
Danh sách học sinh tối giản để render grid.

**Response data:**
```json
{
  "items": [
    { "student_id": 301, "student_code": "HS0301", "full_name": "Nguyễn An" }
  ]
}
```

---

### GET `/teacher/gradebook/matrix`
Bảng điểm dạng ma trận (1 call).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `class_subject_id` | int | Bắt buộc |

**Response data:**
```json
{
  "class_subject_id": 501,
  "rounding": { "scale": "standard", "precision": 1, "rule": "round_half_up" },
  "components": [
    { "grade_component_id": 1001, "name": "15 phút", "weight_percent": 10, "min_count": 2 }
  ],
  "students": [
    { "student_id": 301, "student_code": "HS0301", "full_name": "Nguyễn An" }
  ],
  "scores": [
    { "student_id": 301, "grade_component_id": 1001, "score": 8.5, "exam_date": "2026-03-10" }
  ],
  "averages": [
    { "student_id": 301, "average_score": 8.7, "rank": "Gioi" }
  ]
}
```

---

### PATCH `/teacher/gradebook/entries`
Ghi điểm hàng loạt (batch upsert).

**Body:**
```json
{
  "class_subject_id": 501,
  "items": [
    { "student_id": 301, "grade_component_id": 1001, "score": 9.0, "exam_date": "2026-03-10" }
  ]
}
```

**Response data:**
```json
{ "created": 1, "updated": 0 }
```

---

### GET `/teacher/attendance/matrix`
Bảng điểm danh dạng ma trận (1 call).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `classroom_id` | int | Bắt buộc |
| `date_from` | date | YYYY-MM-DD |
| `date_to` | date | YYYY-MM-DD |

**Response data:**
```json
{
  "classroom_id": 18,
  "date_from": "2026-03-01",
  "date_to": "2026-03-31",
  "cycle_order": ["present", "late", "absent_excused", "absent_unexcused"],
  "students": [
    { "student_id": 301, "student_code": "HS0301", "full_name": "Nguyễn An", "absence_rate": 0.12 }
  ],
  "records": [
    { "student_id": 301, "date": "2026-03-03", "status": "present", "note": "" }
  ]
}
```

---

### PATCH `/teacher/attendance/entries`
Cập nhật điểm danh hàng loạt.

**Body:**
```json
{
  "classroom_id": 18,
  "items": [
    { "student_id": 301, "date": "2026-03-03", "status": "absent_unexcused", "note": "No show" }
  ]
}
```

**Response data:**
```json
{ "created": 0, "updated": 1 }
```

---

### GET `/teacher/timetable`
Lịch dạy tuần/tháng.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `from` | datetime | ISO 8601 |
| `to` | datetime | ISO 8601 |
| `view` | string | `week` hoặc `month` |

**Response data:**
```json
{
  "items": [
    {
      "id": 9001,
      "start": "2026-03-11T08:00:00",
      "end": "2026-03-11T09:30:00",
      "classroom_id": 18,
      "class_name": "Lớp 10A1",
      "subject_name": "Toán",
      "room_number": "A-302"
    }
  ]
}
```


---

## 18. Auth

**Bootstrap admin:** cần seed bảng `users` bằng mật khẩu đã hash (dùng `app.core.security.get_password_hash`).


### POST `/auth/login`
Đăng nhập lấy JWT.

**Body:**
```json
{
  "username": "admin",
  "password": "secret"
}
```

**Response data:**
```json
{
  "access_token": "jwt...",
  "refresh_token": "jwt_refresh...",
  "token_type": "bearer",
  "expires_in": 3600,
  "role": "admin",
  "user_id": 1,
  "teacher_id": 45
}
```

---

### POST `/auth/refresh`
Làm mới access token từ refresh token.

**Body:**
```json
{ "refresh_token": "jwt_refresh..." }
```

**Response:** Giống `/auth/login` (access + refresh mới).

---

### POST `/auth/logout`
Logout (blacklist token).

**Body:**
```json
{ "token": "jwt...", "token_type": "access" }
```

---

### POST `/auth/users` (admin)
Tạo user.

**Body:**
```json
{
  "username": "teacher01",
  "password": "secret123",
  "role": "teacher",
  "teacher_id": 45
}
```

---

### GET `/auth/users` (admin)
Danh sách user.

**Query params:** `role`, `is_active`, `page`, `page_size`

---

### GET `/auth/users/{user_id}` (admin)
Chi tiết user.

---

### PATCH `/auth/users/{user_id}` (admin)
Cập nhật user.

**Body:**
```json
{ "password": "newpass", "is_active": true }
```

**Header dùng cho endpoint bảo vệ:**
```
Authorization: Bearer <access_token>
```

**JWT payload tối thiểu:**
```json
{ "sub": "1", "role": "teacher", "teacher_id": 45, "type": "access", "jti": "..." }
```

**ENV:**
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM` (default: HS256)
- `JWT_EXPIRE_MINUTES` (default: 60)
- `JWT_REFRESH_EXPIRE_MINUTES` (default: 43200)

---
## 19. Admin Timetable & Attendance

> Namespace: `/api/v1/admin/*`  (RBAC: role `admin`)

### GET `/admin/timetable`
**Query params:** `from`, `to`, `teacher_id` (optional)

### POST `/admin/timetable`
Tạo lịch dạy cho giáo viên.

**Body:**
```json
{
  "teacher_id": 45,
  "classroom_id": 18,
  "class_subject_id": 501,
  "subject_id": 7,
  "start_time": "2026-03-11T08:00:00",
  "end_time": "2026-03-11T09:30:00",
  "room_number": "A-302",
  "note": "Tiết chính khóa"
}
```

### PATCH `/admin/timetable/{entry_id}`
Cập nhật lịch dạy (partial).

### DELETE `/admin/timetable/{entry_id}`
Xóa mềm lịch dạy.

---

### GET `/admin/attendance/matrix`
**Query params:** `classroom_id`, `date_from`, `date_to`

### PATCH `/admin/attendance/entries`
Ghi điểm danh hàng loạt (admin).

**Body:**
```json
{
  "classroom_id": 18,
  "recorded_by": 45,
  "items": [
    { "student_id": 301, "date": "2026-03-03", "status": "present", "note": "" }
  ]
}
```

---

## 20. Lookups

> Namespace: `/api/v1/lookups/*`  (RBAC: role `admin`)

### GET `/lookups/teachers`
Danh sách giáo viên tối giản cho dropdown.

**Query params:** `search` (optional, search by code/name)

**Response data:**
```json
{
  "items": [
    { "id": 1, "teacher_code": "GV0001", "full_name": "Tran Thi Mai" }
  ]
}
```

---

### GET `/lookups/classrooms`
Danh sách lớp học tối giản.

**Query params:** `search` (optional, search by code/name)

**Response data:**
```json
{
  "items": [
    { "id": 18, "class_code": "10A1-2025", "class_name": "Lớp 10A1", "grade_level": 10, "academic_year": "2025-2026" }
  ]
}
```

---

### GET `/lookups/students`
Danh sách học sinh tối giản.

**Query params:** `search` (optional, search by code/name)

**Response data:**
```json
{
  "items": [
    { "id": 301, "student_code": "HS0301", "full_name": "Nguyễn An", "class_name": "10A1" }
  ]
}
```

---

### GET `/lookups/subjects`
Danh sách môn học tối giản.

**Query params:** `search` (optional, search by code/name)

**Response data:**
```json
{
  "items": [
    { "id": 7, "subject_code": "TOAN", "subject_name": "Toán" }
  ]
}
```


