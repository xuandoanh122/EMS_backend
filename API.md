# EMS Backend – API Reference

> Base URL: `http://localhost:8000/api/v1`  
> Tất cả response đều bọc trong envelope `APIResponse`:
> ```json
> { "code": 200, "message": "OK", "detail": "...", "data": { ... }, "errors": null }
> ```

---

## Mục lục

1. [System](#1-system)
2. [Dashboard](#2-dashboard)
3. [Students](#3-students)
4. [Teachers](#4-teachers)
5. [Classrooms](#5-classrooms)
6. [Enrollments](#6-enrollments-lồng-trong-classrooms)
7. [Grading – Subjects](#7-grading--subjects)
8. [Grading – Class Subjects](#8-grading--class-subjects-phân-công)
9. [Grading – Grade Components](#9-grading--grade-components)
10. [Grading – Student Grades](#10-grading--student-grades)
11. [Grading – Reports & Statistics](#11-grading--reports--statistics)
12. [Salary – Salary Grades](#12-salary--salary-grades)
13. [Salary – Bonus Policies](#13-salary--bonus-policies)
14. [Salary – Payrolls](#14-salary--payrolls)
15. [Enums Reference](#15-enums-reference)
16. [Business Logic & Luồng xử lý](#16-business-logic--luồng-xử-lý)

---

## 1. System

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/health` | Health check |

---

## 2. Dashboard

### GET `/dashboard/stats`
Thống kê tổng quan hệ thống.

**Response data:**
```json
{
  "total_students": 120,
  "total_teachers": 15,
  "total_classrooms": 8,
  "active_students": 110,
  "active_teachers": 13,
  "recent_students": [ ...5 học sinh mới nhất... ],
  "recent_teachers": [ ...5 giáo viên mới nhất... ]
}
```

---

## 3. Students

### POST `/students`
Tạo học sinh mới.

**Body (required: `*`):**
```json
{
  "student_code": "SV2024001",       // * unique, max 20 ký tự
  "full_name": "Nguyen Van An",      // * max 150 ký tự
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
Danh sách học sinh (phân trang + lọc).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `search` | string | Tìm theo `student_code`, `full_name`, `email` |
| `academic_status` | enum | `active` \| `preserved` \| `suspended` \| `graduated` |
| `class_name` | string | Lọc theo lớp |
| `program_name` | string | Lọc theo chương trình |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–100 | Mặc định: 20 |

---

### GET `/students/{student_code}`
Chi tiết 1 học sinh theo mã.

---

### PATCH `/students/{student_code}`
Cập nhật thông tin học sinh (partial update – chỉ gửi fields cần sửa).

**Body:** Tất cả fields đều optional (giống Create nhưng không có `student_code`):
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
Thay đổi trạng thái học vụ.

**Body:**
```json
{
  "new_status": "preserved",   // * enum StudentStatus
  "reason": "Nghỉ học vì lý do cá nhân"  // optional
}
```

**Luồng chuyển trạng thái hợp lệ:**
```
active → preserved | suspended | graduated
preserved → active | suspended
suspended → active
graduated → (terminal – không thể chuyển)
```

---

### DELETE `/students/{student_code}`
Soft-delete học sinh (`is_active = false`). Dữ liệu vẫn giữ lại trong DB.

---

## 4. Teachers

### POST `/teachers`
Tạo giáo viên mới.

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
  "specialization": "Toán học",      // optional, max 200
  "qualification": "Thạc sĩ",        // optional, max 200
  "department": "Khoa học tự nhiên"  // optional, max 200
}
```

---

### GET `/teachers`
Danh sách giáo viên (phân trang + lọc).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `search` | string | Tìm theo `teacher_code`, `full_name`, `email` |
| `employment_status` | enum | `active` \| `on_leave` \| `resigned` \| `retired` |
| `department` | string | Lọc theo phòng ban |
| `specialization` | string | Lọc theo chuyên môn |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–100 | Mặc định: 20 |

---

### GET `/teachers/{teacher_code}`
Chi tiết 1 giáo viên.

---

### PATCH `/teachers/{teacher_code}`
Cập nhật thông tin giáo viên (partial update).

**Body:** Tất cả fields optional (không có `teacher_code`):
```json
{
  "phone_number": "0909999888",
  "department": "Khoa học xã hội",
  "join_date": "2024-01-01"
}
```

---

### PATCH `/teachers/{teacher_code}/status`
Thay đổi trạng thái công tác.

**Body:**
```json
{
  "new_status": "on_leave",        // * enum TeacherStatus
  "reason": "Nghỉ thai sản 6 tháng"  // optional
}
```

**Luồng chuyển trạng thái hợp lệ:**
```
active → on_leave | resigned | retired
on_leave → active | resigned
resigned → (terminal)
retired → (terminal)
```

---

### DELETE `/teachers/{teacher_code}`
Soft-delete giáo viên.

---

## 5. Classrooms

### POST `/classrooms`
Tạo lớp học mới.

**Body (required: `*`):**
```json
{
  "class_code": "10A1-2024",         // * unique, max 30
  "class_name": "Lớp 10A1",          // * max 100
  "class_type": "standard",          // optional, default: "standard"
  "academic_year": "2024-2025",      // * format "YYYY-YYYY"
  "grade_level": 10,                 // * integer 1–13
  "max_capacity": 40,                // optional, default: 40 (1–200)
  "homeroom_teacher_id": 3,          // optional, FK → teachers.id
  "room_number": "P.201",            // optional, max 20
  "description": "..."               // optional, max 300
}
```

> **Logic:** `class_code` phải unique. Hệ thống tự track `current_enrollment` (không nhập tay).

---

### GET `/classrooms`
Danh sách lớp học (phân trang + lọc).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `search` | string | Tìm theo `class_code` hoặc `class_name` |
| `class_type` | enum | `standard` \| `specialized` \| `advanced` |
| `academic_year` | string | VD: `"2024-2025"` |
| `grade_level` | int 1–13 | Khối lớp |
| `homeroom_teacher_id` | int | ID giáo viên chủ nhiệm |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–100 | Mặc định: 20 |

---

### GET `/classrooms/{class_code}`
Chi tiết 1 lớp học.

---

### PATCH `/classrooms/{class_code}`
Cập nhật thông tin lớp học.

**Body:** Tất cả fields optional:
```json
{
  "room_number": "P.305",
  "max_capacity": 35,
  "homeroom_teacher_id": 3,
  "description": "..."
}
```

---

### DELETE `/classrooms/{class_code}`
Soft-delete lớp học.

---

## 6. Enrollments (lồng trong Classrooms)

### POST `/classrooms/{class_code}/enrollments`
Đăng ký học sinh vào lớp.

**Path:** `class_code` – mã lớp (string).

**Body (required: `*`):**
```json
{
  "student_id": 1,                   // * FK → students.id
  "classroom_id": 2,                 // * FK → classrooms.id (sẽ bị override bởi path param)
  "enrollment_type": "primary",      // optional, default: "primary"
  "enrolled_date": "2024-09-01",     // optional
  "notes": "Chuyển đến từ trường khác"  // optional, max 300
}
```

> **Logic nghiệp vụ:**
> 1. Kiểm tra lớp tồn tại (theo `class_code`).
> 2. Kiểm tra `current_enrollment < max_capacity` → nếu đầy: `ClassroomCapacityExceeded`.
> 3. Nếu `enrollment_type = "primary"`: kiểm tra học sinh chưa có lớp chính nào đang active → nếu có: `DuplicatePrimaryEnrollment`.
> 4. Kiểm tra không trùng lặp cùng loại enrollment trong cùng lớp → `EnrollmentAlreadyExists`.

---

### GET `/classrooms/{class_code}/enrollments`
Danh sách học sinh trong lớp.

**Path:** `class_code` – mã lớp.

**Query params:**
| Param | Type | Mặc định |
|-------|------|---------|
| `page` | int ≥ 1 | 1 |
| `page_size` | int 1–200 | 50 |

---

### GET `/classrooms/enrollments/{enrollment_id}`
Chi tiết 1 bản ghi enrollment.

---

### PATCH `/classrooms/enrollments/{enrollment_id}`
Cập nhật ghi chú enrollment.

**Body:**
```json
{
  "notes": "Học sinh chuyển đến từ trường khác"  // optional, max 300
}
```

---

### PATCH `/classrooms/enrollments/{enrollment_id}/status`
Thay đổi trạng thái enrollment.

**Body:**
```json
{
  "new_status": "transferred",       // * enum EnrollmentStatus
  "left_date": "2024-12-01",         // optional
  "notes": "Chuyển sang lớp 10A2"    // optional, max 300
}
```

**Luồng chuyển trạng thái hợp lệ:**
```
active → transferred | withdrawn | completed
transferred → (terminal)
withdrawn → (terminal)
completed → (terminal)
```

---

### GET `/classrooms/students/{student_id}/enrollments`
Tất cả lớp mà 1 học sinh đang/đã tham gia.

---

## 7. Grading – Subjects

### POST `/grading/subjects`
Tạo môn học.

**Body (required: `*`):**
```json
{
  "subject_code": "TOAN",            // * unique, max 20
  "subject_name": "Toán học",        // * max 100
  "subject_type": "standard",        // optional, default: "standard"
  "credits": 4,                      // optional, default: 1 (1–10)
  "description": "..."               // optional, max 300
}
```

---

### GET `/grading/subjects`
Danh sách môn học.

**Query params:**
| Param | Type | Mặc định |
|-------|------|---------|
| `page` | int ≥ 1 | 1 |
| `page_size` | int 1–100 | 20 |
| `active_only` | bool | `true` |

---

### GET `/grading/subjects/{subject_code}`
Chi tiết môn học.

---

### PATCH `/grading/subjects/{subject_code}`
Cập nhật môn học.

**Body:** Tất cả optional:
```json
{
  "subject_name": "Toán cao cấp",
  "credits": 5,
  "description": "...",
  "is_active": true
}
```

---

## 8. Grading – Class Subjects (Phân công)

> **Class Subject** = Môn học được phân công dạy tại 1 lớp, 1 học kỳ, bởi 1 giáo viên.  
> Đây là đơn vị gốc để nhập điểm.

### POST `/grading/class-subjects`
Phân công môn học cho lớp + giáo viên.

**Body (required: `*`):**
```json
{
  "classroom_id": 1,                 // * FK → classrooms.id
  "subject_id": 2,                   // * FK → subjects.id
  "teacher_id": 3,                   // optional, FK → teachers.id
  "semester": 1,                     // * 1 hoặc 2
  "academic_year": "2024-2025"       // * format "YYYY-YYYY"
}
```

> **Logic:** Không được tạo trùng `(classroom_id, subject_id, semester, academic_year)`.

---

### GET `/grading/class-subjects`
Danh sách phân công môn.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `classroom_id` | int | Lọc theo lớp |
| `teacher_id` | int | Lọc theo giáo viên |
| `academic_year` | string | VD: `"2024-2025"` |
| `semester` | int 1–2 | Học kỳ |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–200 | Mặc định: 50 |

---

### GET `/grading/class-subjects/{cs_id}`
Chi tiết phân công môn.

---

### PATCH `/grading/class-subjects/{cs_id}`
Cập nhật phân công (đổi/gán giáo viên, bật/tắt).

**Body:**
```json
{
  "teacher_id": 5,     // optional
  "is_active": true    // optional
}
```

---

## 9. Grading – Grade Components

> **Grade Component** = Thành phần điểm (miệng, 15 phút, 1 tiết, học kỳ…) của 1 Class Subject.  
> Mỗi component có trọng số (`weight_percent`). Tổng weight của các component trong 1 class-subject nên = 100%.

### POST `/grading/grade-components`
Tạo thành phần điểm.

**Body (required: `*`):**
```json
{
  "class_subject_id": 1,             // * FK → class_subjects.id
  "component_name": "Kiểm tra miệng", // * max 100
  "weight_percent": 10,              // * 1–100 (%)
  "min_count": 2                     // optional, default: 1 – số bài tối thiểu
}
```

---

### GET `/grading/grade-components/{class_subject_id}`
Danh sách thành phần điểm của 1 class-subject.

---

### PATCH `/grading/grade-components/{gc_id}`
Cập nhật thành phần điểm.

**Body:** Tất cả optional:
```json
{
  "component_name": "Kiểm tra 15 phút",
  "weight_percent": 15,
  "min_count": 3,
  "is_active": true
}
```

---

## 10. Grading – Student Grades

> **Điều kiện trước:** Phải có `class_subject_id` và `grade_component_id` tương ứng.

### POST `/grading/grades`
Nhập điểm cho 1 học sinh.

**Body (required: `*`):**
```json
{
  "student_id": 1,                   // * FK → students.id
  "class_subject_id": 3,             // * FK → class_subjects.id
  "grade_component_id": 2,           // * FK → grade_components.id
  "score": 8.5,                      // * 0–10 (decimal)
  "exam_date": "2024-11-10",         // optional
  "entered_by": 4                    // optional – ID giáo viên nhập điểm
}
```

> **Logic:** Không cho phép nhập trùng `(student_id, class_subject_id, grade_component_id)`.

---

### POST `/grading/grades/bulk`
Nhập điểm hàng loạt (nhiều học sinh, cùng 1 cột điểm).

**Body (required: `*`):**
```json
{
  "class_subject_id": 3,             // *
  "grade_component_id": 2,           // *
  "exam_date": "2024-11-10",         // optional
  "entered_by": 4,                   // optional
  "grades": [                        // * danh sách điểm
    { "student_id": 1, "score": 8.5 },
    { "student_id": 2, "score": 7.0 },
    { "student_id": 3, "score": 9.0 }
  ]
}
```

---

### GET `/grading/grades/{grade_id}`
Chi tiết 1 bản ghi điểm.

---

### PATCH `/grading/grades/{grade_id}`
Sửa điểm (bắt buộc có lý do – ghi audit log tự động).

**Body (required: `*`):**
```json
{
  "score": 9.0,                      // * 0–10
  "reason": "Chấm sai, đã phúc tra lại",  // * bắt buộc, max 300
  "modified_by": 4                   // optional – ID giáo viên sửa
}
```

> **Logic:** Mỗi lần sửa tạo 1 bản ghi `GradeAuditLog` lưu điểm cũ, điểm mới, lý do.

---

### GET `/grading/grades/{grade_id}/audit-logs`
Lịch sử thay đổi điểm của 1 bản ghi.

---

### GET `/grading/class-subjects/{cs_id}/grades`
Tất cả điểm trong 1 class-subject.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `grade_component_id` | int | Lọc theo cột điểm |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–500 | Mặc định: 100 |

---

## 11. Grading – Reports & Statistics

### GET `/grading/students/{student_id}/report`
Báo cáo điểm học sinh theo học kỳ.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `semester` | int 1–2 | Lọc theo học kỳ |
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
Thống kê điểm của cả lớp cho 1 môn học.

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

## 12. Salary – Salary Grades

> **Salary Grade** = Ngạch lương, định nghĩa mức lương cơ bản và đơn giá tiết dạy theo trình độ + thâm niên.

### POST `/salary/grades`
Tạo ngạch lương.

**Body (required: `*`):**
```json
{
  "grade_code": "THAC_SI_3_6NAM",    // * unique, max 30
  "qualification_level": "thac_si",  // * enum QualificationLevel
  "experience_tier": "3_to_6y",      // * enum ExperienceTier
  "base_salary": 8500000,            // * VNĐ/tháng, ≥ 0
  "hourly_rate": 85000,              // * VNĐ/tiết, ≥ 0
  "effective_from": "2024-01-01",    // * YYYY-MM-DD
  "effective_to": null,              // optional
  "description": "..."               // optional, max 300
}
```

---

### GET `/salary/grades`
Danh sách ngạch lương.

**Query params:** `page`, `page_size`, `active_only` (default: `true`).

---

### GET `/salary/grades/{grade_code}`
Chi tiết ngạch lương.

---

### PATCH `/salary/grades/{grade_code}`
Cập nhật ngạch lương.

**Body:** Tất cả optional:
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

## 13. Salary – Bonus Policies

> **Bonus Policy** = Chính sách thưởng tái sử dụng (thưởng thâm niên, thưởng GVCN...).

### POST `/salary/bonus-policies`
Tạo chính sách thưởng.

**Body (required: `*`):**
```json
{
  "policy_code": "THUONG_THAM_NIEN_3NAM",     // * unique, max 30
  "policy_name": "Thưởng đạt mốc 3 năm",      // * max 200
  "bonus_type": "fixed",                        // optional, default: "fixed"
  "bonus_value": 500000,                        // * ≥ 0
  "condition_description": "..."               // optional, max 500
}
```

---

### GET `/salary/bonus-policies`
Danh sách chính sách thưởng.

**Query params:** `page`, `page_size`, `active_only` (default: `true`).

---

### GET `/salary/bonus-policies/{policy_code}`
Chi tiết chính sách thưởng.

---

### PATCH `/salary/bonus-policies/{policy_code}`
Cập nhật chính sách thưởng.

**Body:** Tất cả optional:
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

## 14. Salary – Payrolls

> **Payroll** = Bảng lương tháng của 1 giáo viên. Trải qua 3 trạng thái: `draft → confirmed → paid`.

### POST `/salary/payrolls`
Tạo bảng lương tháng.

**Body (required: `*`):**
```json
{
  "teacher_id": 1,                   // * FK → teachers.id
  "salary_grade_id": 2,              // * FK → salary_grades.id
  "payroll_month": "2024-09-01",     // * lưu ngày 1 của tháng, YYYY-MM-DD
  "work_days_standard": 22,          // optional, default: 22
  "work_days_actual": 21,            // optional, default: 0
  "teaching_hours_standard": 80,     // optional, default: 0
  "teaching_hours_actual": 90,       // optional, default: 0
  "base_salary": 8500000,            // optional, default: 0
  "teaching_allowance": 850000,      // optional, default: 0
  "deductions": 0,                   // optional, default: 0
  "notes": "...",                    // optional, max 500
  "bonus_details": [                 // optional, danh sách khoản thưởng đính kèm
    {
      "bonus_policy_id": 1,          // * FK → bonus_policies.id
      "amount": 500000,              // * ≥ 0
      "note": "Thưởng thâm niên"     // optional, max 300
    }
  ]
}
```

> **Logic:** `net_salary = base_salary + teaching_allowance + total_bonus - deductions`. Tự tính khi tạo/cập nhật.

---

### GET `/salary/payrolls`
Danh sách bảng lương (có lọc).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `teacher_id` | int | Lọc theo giáo viên |
| `status` | enum | `draft` \| `confirmed` \| `paid` |
| `month_from` | YYYY-MM-DD | Lọc từ tháng |
| `month_to` | YYYY-MM-DD | Lọc đến tháng |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–100 | Mặc định: 20 |

---

### GET `/salary/payrolls/{payroll_id}`
Chi tiết bảng lương (bao gồm danh sách `bonus_details`).

---

### PATCH `/salary/payrolls/{payroll_id}`
Cập nhật bảng lương (chỉ cho phép khi status = `draft`).

**Body:** Tất cả optional:
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
Duyệt / thanh toán bảng lương.

**Body:**
```json
{
  "new_status": "confirmed",         // * enum PayrollStatus
  "confirmed_by": 5,                 // optional – ID người duyệt
  "notes": "Đã kiểm tra, duyệt chi"  // optional, max 500
}
```

**Luồng chuyển trạng thái hợp lệ:**
```
draft → confirmed
confirmed → paid
paid → (terminal)
```

---

### POST `/salary/payrolls/{payroll_id}/bonuses`
Thêm khoản thưởng vào bảng lương (chỉ khi chưa `paid`).

**Body:**
```json
{
  "bonus_policy_id": 1,              // * FK → bonus_policies.id
  "amount": 500000,                  // * ≥ 0
  "note": "Thưởng GVCN"             // optional, max 300
}
```

> **Logic:** Sau khi thêm bonus, `total_bonus` và `net_salary` được tính lại tự động.

---

## 15. Enums Reference

### StudentStatus
| Value | Ý nghĩa |
|-------|---------|
| `active` | Đang học |
| `preserved` | Bảo lưu |
| `suspended` | Đình chỉ |
| `graduated` | Đã tốt nghiệp |

### TeacherStatus
| Value | Ý nghĩa |
|-------|---------|
| `active` | Đang công tác |
| `on_leave` | Đang nghỉ phép |
| `resigned` | Đã nghỉ việc |
| `retired` | Đã về hưu |

### ClassType
| Value | Ý nghĩa |
|-------|---------|
| `standard` | Lớp thường |
| `specialized` | Lớp chuyên |
| `advanced` | Lớp nâng cao |

### EnrollmentType
| Value | Ý nghĩa |
|-------|---------|
| `primary` | Lớp chính (mỗi HS chỉ có 1) |
| `secondary` | Lớp phụ / câu lạc bộ |

### EnrollmentStatus
| Value | Ý nghĩa |
|-------|---------|
| `active` | Đang học |
| `transferred` | Đã chuyển lớp |
| `withdrawn` | Đã rút khỏi lớp |
| `completed` | Hoàn thành |

### SubjectType
| Value | Ý nghĩa |
|-------|---------|
| `standard` | Môn bắt buộc |
| `elective` | Môn tự chọn |
| `extra` | Môn ngoại khóa |

### AcademicRank (xếp loại)
| Value | Điểm TB |
|-------|---------|
| `Gioi` | ≥ 8.0 |
| `Kha` | 6.5–7.9 |
| `TrungBinh` | 5.0–6.4 |
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

## 16. Business Logic & Luồng xử lý

### Luồng hoàn chỉnh: Nhập điểm cho 1 lớp

```
1. Tạo Teacher          POST /teachers
2. Tạo Classroom        POST /classrooms
3. Enroll Students      POST /classrooms/{class_code}/enrollments  (mỗi HS)
4. Tạo Subject          POST /grading/subjects
5. Phân công dạy        POST /grading/class-subjects
      └─ classroom_id + subject_id + teacher_id + semester + academic_year
6. Cấu hình thành phần điểm
                        POST /grading/grade-components  (mỗi cột: miệng, 15p, 1tiết, HK...)
7. Nhập điểm            POST /grading/grades  hoặc  POST /grading/grades/bulk
8. Xem báo cáo học sinh GET /grading/students/{student_id}/report
9. Xem thống kê lớp     GET /grading/class-subjects/{cs_id}/statistics
```

### Luồng hoàn chỉnh: Xử lý lương giáo viên

```
1. Tạo SalaryGrade      POST /salary/grades
      └─ qualification_level + experience_tier + base_salary + hourly_rate
2. Tạo BonusPolicy      POST /salary/bonus-policies  (nếu có thưởng)
3. Tạo Payroll tháng    POST /salary/payrolls
      └─ teacher_id + salary_grade_id + payroll_month + giờ dạy + khấu trừ + bonus
4. Duyệt payroll        PATCH /salary/payrolls/{id}/status  { "new_status": "confirmed" }
5. Thanh toán           PATCH /salary/payrolls/{id}/status  { "new_status": "paid" }
```

### Ràng buộc quan trọng

| Ràng buộc | Mô tả |
|-----------|-------|
| `student_code`, `teacher_code`, `class_code`, `subject_code` | Unique trong toàn hệ thống |
| `email`, `national_id` (student/teacher) | Unique nếu có giá trị |
| Enrollment PRIMARY | Mỗi học sinh chỉ được có 1 lớp primary active tại 1 thời điểm |
| Enrollment capacity | Không thể enroll khi `current_enrollment >= max_capacity` |
| Grade unique | `(student_id, class_subject_id, grade_component_id)` unique |
| Grade audit | Mọi thao tác sửa điểm đều bắt buộc `reason` và tạo audit log |
| Payroll editable | Chỉ cập nhật/thêm bonus khi `status != paid` |
| Status transition | Mọi chuyển trạng thái đều có whitelist hợp lệ, vi phạm trả lỗi |
| Soft-delete | Không xóa cứng bất kỳ record nào – chỉ set `is_active = false` |
