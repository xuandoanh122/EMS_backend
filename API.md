# EMS – API Reference & FE/BE Contract

> Base URL: `http://localhost:8000/api/v1`
> Tất cả response đều bọc trong envelope `APIResponse`:
> ```json
> { "code": 200, "message": "OK", "detail": "...", "data": { ... }, "errors": null }
> ```

---

## Mục lục

1. [Nguyên tắc phân công FE / BE](#1-nguyên-tắc-phân-công-fe--be)
2. [System & Lookups](#2-system--lookups)
3. [Dashboard](#3-dashboard)
4. [Students](#4-students)
5. [Teachers](#5-teachers)
6. [Classrooms](#6-classrooms)
7. [Enrollments](#7-enrollments)
8. [Grading – Subjects](#8-grading--subjects)
9. [Grading – Class Subjects (Phân công)](#9-grading--class-subjects-phân-công)
10. [Grading – Grade Components](#10-grading--grade-components)
11. [Grading – Student Grades](#11-grading--student-grades)
12. [Grading – Reports & Statistics](#12-grading--reports--statistics)
13. [Salary – Salary Grades](#13-salary--salary-grades)
14. [Salary – Bonus Policies](#14-salary--bonus-policies)
15. [Salary – Payrolls](#15-salary--payrolls)
16. [Enums Reference](#16-enums-reference)
17. [Business Logic & Luồng xử lý đầy đủ](#17-business-logic--luồng-xử-lý-đầy-đủ)

---

## 1. Nguyên tắc phân công FE / BE

### Quy tắc vàng (không được vi phạm)

| # | Quy tắc | FE làm | BE làm |
|---|---------|--------|--------|
| 1 | **Auto-generate ID** | KHÔNG hiển thị ô nhập `student_code` / `teacher_code` khi tạo mới. Hiển thị placeholder "Hệ thống tự cấp mã" | Sinh mã tự động theo format `StudYYMMxxx` / `TchrYYMMxxx` trước khi INSERT |
| 2 | **Khóa ngoại = Dropdown** | Mọi FK field (teacher_id, classroom_id, subject_id...) phải dùng Select/Combobox gọi từ Lookup API – KHÔNG bắt user gõ số ID | Cung cấp các `GET /lookups/...` trả về `[{id, label}]` gọn nhẹ |
| 3 | **Validation 2 lớp** | Validate ở Zod schema (FE) trước khi gửi request – bắt lỗi format, required field ngay tại form | Validate ở Pydantic DTO (BE) và business rule – là lớp chặn cuối cùng |
| 4 | **Transaction phức tạp** | Chỉ gọi 1 API duy nhất cho các luồng liên quan nhiều bảng (VD: tạo HS + xếp lớp) | Bọc toàn bộ luồng trong DB Transaction – rollback nếu bất kỳ bước nào lỗi |
| 5 | **Trạng thái & chuyển trạng thái** | Chỉ hiển thị các lựa chọn transition hợp lệ dựa trên whitelist | Kiểm tra lại whitelist ở BE – từ chối nếu FE gửi transition không hợp lệ |
| 6 | **Soft-delete** | Hiển thị confirm dialog trước khi xóa. Sau khi xóa, remove item khỏi danh sách local (optimistic) hoặc refetch | KHÔNG xóa cứng. Chỉ set `is_active = false` |

### Bảng phân công theo module

| Module | Công việc FE | Công việc BE | Trạng thái |
|--------|-------------|-------------|------------|
| **Students** | Xóa ô nhập `student_code` ở Create form. Thêm Multi-select Dropdown chọn lớp khi tạo HS. Thêm filter "Chờ xếp lớp" | Sinh mã `StudYYMMxxx` auto. Tích hợp enroll vào 1 Transaction | `student_code` vẫn required ở FE – **cần sửa** |
| **Teachers** | Xóa ô nhập `teacher_code`. Đổi `specialization` text → Dropdown | Sinh mã `TchrYYMMxxx` auto | `teacher_code` vẫn required ở FE – **cần sửa** |
| **Classrooms** | Đổi `homeroom_teacher_id` thành Dropdown chọn tên GV. Thêm tab "Học sinh" và "Phân công môn" trong detail | Cung cấp `GET /lookups/teachers`. Tự track `current_enrollment` | Enrollment form đang yêu cầu nhập số ID thủ công – **cần sửa** |
| **Enrollments** | Đổi "ID học sinh" input → Combobox tìm kiếm học sinh theo tên/mã. Hỗ trợ xếp lớp nhanh từ danh sách HS chờ | Cung cấp `GET /lookups/students` có thể search. Kiểm tra conflict TKB (tương lai) | Input đang là số ID thô – **cần sửa ngay** |
| **Grading** | Giao diện bảng điểm dạng Grid (giống Excel). Dropdown chọn lớp → tự load danh sách HS và cột điểm | Cung cấp `GET /grading/class-subjects/{cs_id}/grade-matrix` trả về ma trận HS × điểm | Chưa có grade matrix endpoint – **BE cần thêm** |
| **Salary** | Dropdown chọn GV, chọn Salary Grade. Tự tính preview `net_salary` ở FE trước khi submit | Tính lại `net_salary` ở BE khi tạo/cập nhật – FE preview chỉ để UX | Cơ bản ổn, cần thêm preview |

---

## 2. System & Lookups

### GET `/health`
Health check.

---

### Lookup APIs (BE cần tạo mới – FE dùng cho Dropdown)

> Các API này trả về danh sách gọn `{id, label}` để FE render Dropdown/Combobox.
> Không cần phân trang – giới hạn 200 items.

| Method | Path | Mô tả | Dùng ở đâu |
|--------|------|-------|-----------|
| GET | `/lookups/teachers` | Danh sách GV đang active | Dropdown chọn GVCN, phân công lớp |
| GET | `/lookups/classrooms` | Danh sách lớp đang active | Dropdown chọn lớp khi tạo HS, tạo enrollment |
| GET | `/lookups/students` | Tìm kiếm HS theo tên/mã | Combobox thêm HS vào lớp |
| GET | `/lookups/subjects` | Danh sách môn học đang active | Dropdown phân công môn |

**Query params chung cho lookups:**
| Param | Type | Mô tả |
|-------|------|-------|
| `search` | string | Tìm kiếm theo tên hoặc mã (optional) |
| `limit` | int | Mặc định: 100, tối đa: 200 |

**Response mẫu `GET /lookups/teachers`:**
```json
{
  "data": [
    { "id": 1, "label": "Trần Thị Mai", "sub_label": "Tchr2603001" },
    { "id": 2, "label": "Nguyễn Văn Hùng", "sub_label": "Tchr2603002" }
  ]
}
```

**Response mẫu `GET /lookups/students`:**
```json
{
  "data": [
    { "id": 1, "label": "Nguyễn Văn An", "sub_label": "Stud2603001 · Lớp IELTS Basic" },
    { "id": 2, "label": "Trần Thị B", "sub_label": "Stud2603002 · Chờ xếp lớp" }
  ]
}
```

---

## 3. Dashboard

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
  "pending_enrollment_students": 5,
  "recent_students": [ ...5 học sinh mới nhất... ],
  "recent_teachers": [ ...5 giáo viên mới nhất... ]
}
```

> **FE:** Hiển thị thêm card "Học sinh chờ xếp lớp" (`pending_enrollment_students`) để admin biết cần xử lý.
> **BE:** Thêm field `pending_enrollment_students` vào response (đếm HS có `academic_status = active` nhưng chưa có enrollment active nào).

---

## 4. Students

### Quy tắc mã học sinh
- Format: `Stud` + `YYMM` + `xxx` (3 chữ số STT trong tháng, zero-padded)
- Ví dụ: `Stud2603001` = học sinh thứ 1 được tạo trong tháng 03/2026
- **BE tự sinh** khi nhận `POST /students` – FE không gửi field này

---

### POST `/students`
Tạo học sinh mới. Hỗ trợ xếp lớp ngay trong cùng 1 request.

**FE gửi (required: `*`):**
```json
{
  "full_name": "Nguyen Van An",
  "date_of_birth": "2006-05-15",
  "gender": "male",
  "national_id": "012345678901",
  "email": "an@student.edu.vn",
  "phone_number": "0901234567",
  "address": "...",
  "enrollment_date": "2026-03-01",
  "parent_full_name": "Nguyen Van B",
  "parent_phone": "0912345678",
  "parent_email": "parent@example.com",
  "medical_notes": "...",

  "class_ids": [1, 5]
}
```

> **FE cần sửa:**
> - Xóa field `student_code` khỏi form và Zod schema
> - Xóa field `class_name`, `program_name` (text tự gõ) – thay bằng `class_ids` (Multi-select Dropdown gọi `GET /lookups/classrooms`)
> - `class_ids` là optional – người dùng có thể bỏ qua để xếp lớp sau
>
> **BE cần làm:**
> - Sinh `student_code` = `Stud` + YYMM + STT (query max STT tháng hiện tại + 1, dùng SELECT ... FOR UPDATE hoặc sequence để tránh race condition)
> - Bọc toàn bộ (tạo student + tạo enrollments) trong 1 DB Transaction
> - Nếu `class_ids` rỗng → `academic_status = active` nhưng không có enrollment (trạng thái "chờ xếp lớp")
> - Nếu `class_ids` có giá trị → kiểm tra capacity từng lớp, tạo enrollment. Nếu 1 lớp đầy → ghi lỗi partial vào response nhưng KHÔNG rollback toàn bộ (học sinh vẫn được tạo)

**BE trả về (201):**
```json
{
  "code": 201,
  "message": "Tạo học sinh thành công",
  "data": {
    "student_id": 105,
    "student_code": "Stud2603001",
    "full_name": "Nguyen Van An",
    "enrollments": [
      { "classroom_id": 1, "classroom_name": "IELTS Basic T2T4", "status": "success" },
      { "classroom_id": 5, "classroom_name": "TOEIC 650", "status": "failed", "reason": "ClassroomCapacityExceeded" }
    ]
  }
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
| `has_enrollment` | bool | `true` = đang có lớp, `false` = chưa có lớp (chờ xếp) |
| `classroom_id` | int | Lọc HS trong 1 lớp cụ thể |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–100 | Mặc định: 20 |

> **FE cần thêm:** Filter "Chờ xếp lớp" (`has_enrollment=false`) ở màn hình danh sách HS.
> **BE cần thêm:** Query param `has_enrollment` và `classroom_id`.

---

### GET `/students/{student_code}`
Chi tiết 1 học sinh. Response phải bao gồm danh sách lớp đang học.

**Response data (bổ sung so với hiện tại):**
```json
{
  "student_id": 1,
  "student_code": "Stud2603001",
  "full_name": "Nguyen Van An",
  "...",
  "current_enrollments": [
    {
      "enrollment_id": 10,
      "classroom_id": 1,
      "class_code": "IELTS-B-T2T4",
      "class_name": "IELTS Basic T2T4",
      "enrollment_type": "primary",
      "enrollment_status": "active",
      "enrolled_date": "2026-03-01"
    }
  ]
}
```

> **BE cần bổ sung:** Join với bảng `enrollments` và `classrooms` khi GET detail học sinh.

---

### PATCH `/students/{student_code}`
Cập nhật thông tin học sinh (partial update – chỉ gửi fields cần sửa).

**Body:** Tất cả fields đều optional:
```json
{
  "phone_number": "0909999888",
  "address": "123 Nguyen Hue, Q1",
  "parent_phone": "0911111222"
}
```

> **Lưu ý:** KHÔNG cho phép sửa `student_code` qua API này. `class_name`, `program_name` (text) đã bị loại bỏ – việc thay đổi lớp học phải đi qua Enrollment API.

---

### PATCH `/students/{student_code}/status`
Thay đổi trạng thái học vụ.

**Body:**
```json
{
  "new_status": "preserved",
  "reason": "Nghỉ học vì lý do cá nhân"
}
```

**Luồng chuyển trạng thái hợp lệ:**
```
active → preserved | suspended | graduated
preserved → active | suspended
suspended → active
graduated → (terminal)
```

---

### DELETE `/students/{student_code}`
Soft-delete học sinh (`is_active = false`). Dữ liệu vẫn giữ lại trong DB.

---

## 5. Teachers

### Quy tắc mã giáo viên
- Format: `Tchr` + `YYMM` + `xxx` (3 chữ số STT trong tháng, zero-padded)
- Ví dụ: `Tchr2603001` = giáo viên thứ 1 được tạo trong tháng 03/2026
- **BE tự sinh** khi nhận `POST /teachers` – FE không gửi field này

---

### POST `/teachers`
Tạo giáo viên mới.

**FE gửi (required: `*`):**
```json
{
  "full_name": "Tran Thi Mai",
  "date_of_birth": "1985-03-20",
  "gender": "female",
  "national_id": "098765432101",
  "email": "mai@school.edu.vn",
  "phone_number": "0987654321",
  "address": "...",
  "join_date": "2026-03-01",
  "specialization": "IELTS",
  "qualification": "Thạc sĩ",
  "department": "Tiếng Anh"
}
```

> **FE cần sửa:** Xóa field `teacher_code` khỏi form và Zod schema.
> **BE cần làm:** Sinh `teacher_code` = `Tchr` + YYMM + STT tự động.

**BE trả về (201):**
```json
{
  "code": 201,
  "message": "Tạo giáo viên thành công",
  "data": {
    "teacher_id": 12,
    "teacher_code": "Tchr2603001",
    "full_name": "Tran Thi Mai"
  }
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
Chi tiết 1 giáo viên. Response bao gồm danh sách lớp đang phụ trách.

**Response data (bổ sung):**
```json
{
  "teacher_id": 12,
  "teacher_code": "Tchr2603001",
  "full_name": "Tran Thi Mai",
  "...",
  "teaching_assignments": [
    {
      "cs_id": 3,
      "classroom_id": 1,
      "class_name": "IELTS Basic T2T4",
      "subject_id": 2,
      "subject_name": "IELTS",
      "semester": 1,
      "academic_year": "2025-2026"
    }
  ]
}
```

---

### PATCH `/teachers/{teacher_code}`
Cập nhật thông tin giáo viên (partial update).

**Body:** Tất cả optional (không có `teacher_code`):
```json
{
  "phone_number": "0909999888",
  "department": "Tiếng Anh",
  "specialization": "TOEIC, IELTS"
}
```

---

### PATCH `/teachers/{teacher_code}/status`
Thay đổi trạng thái công tác.

**Body:**
```json
{
  "new_status": "on_leave",
  "reason": "Nghỉ thai sản 6 tháng"
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

## 6. Classrooms

> **Mô hình trung tâm:** 1 lớp = 1 môn học cụ thể (VD: lớp IELTS Basic tối T2T4).
> Giáo viên phụ trách được gán qua Class Subjects (Section 9), không phải trực tiếp trên Classroom.

### POST `/classrooms`
Tạo lớp học mới.

**FE gửi (required: `*`):**
```json
{
  "class_code": "IELTS-B-T2T4-2603",
  "class_name": "IELTS Basic Tối T2T4",
  "class_type": "standard",
  "academic_year": "2025-2026",
  "grade_level": 1,
  "max_capacity": 20,
  "homeroom_teacher_id": 3,
  "room_number": "P.201",
  "description": "Lớp IELTS cơ bản, lịch học tối Thứ 2 và Thứ 4"
}
```

> **FE cần sửa:** Field `homeroom_teacher_id` phải là Dropdown gọi `GET /lookups/teachers` – hiển thị tên GV, gửi ID.
> **BE logic:** `class_code` phải unique. Hệ thống tự track `current_enrollment`.

---

### GET `/classrooms`
Danh sách lớp học (phân trang + lọc).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `search` | string | Tìm theo `class_code` hoặc `class_name` |
| `class_type` | enum | `standard` \| `specialized` \| `advanced` |
| `academic_year` | string | VD: `"2025-2026"` |
| `grade_level` | int | Cấp độ lớp |
| `homeroom_teacher_id` | int | ID giáo viên chủ nhiệm |
| `has_capacity` | bool | `true` = lớp chưa đầy |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–100 | Mặc định: 20 |

> **BE cần thêm:** `has_capacity` filter.

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
  "max_capacity": 25,
  "homeroom_teacher_id": 3,
  "description": "..."
}
```

---

### DELETE `/classrooms/{class_code}`
Soft-delete lớp học.

---

## 7. Enrollments

> Enrollment = Học sinh đăng ký vào 1 lớp học cụ thể.
> 1 học sinh có thể học nhiều lớp (đăng ký nhiều enrollment).
> Mỗi học sinh chỉ có tối đa 1 enrollment `primary` active tại 1 thời điểm.

### POST `/classrooms/{class_code}/enrollments`
Đăng ký học sinh vào lớp.

**FE gửi (required: `*`):**
```json
{
  "student_id": 1,
  "enrollment_type": "primary",
  "enrolled_date": "2026-03-01",
  "notes": "Chuyển từ lớp sáng sang lớp tối"
}
```

> **FE cần sửa ngay (bug UX nghiêm trọng):**
> - Field `student_id` hiện là input số thô → đổi thành **Combobox** gọi `GET /lookups/students?search=...`
> - Combobox hiển thị: `"Nguyen Van An – Stud2603001"`, submit ID số nguyên
> - Xóa field `classroom_id` khỏi body (đã có trong path param `class_code`)

**Logic nghiệp vụ BE:**
1. Kiểm tra lớp tồn tại theo `class_code`.
2. Kiểm tra `current_enrollment < max_capacity` → nếu đầy: lỗi `ClassroomCapacityExceeded`.
3. Nếu `enrollment_type = "primary"`: kiểm tra HS chưa có lớp primary active → nếu có: lỗi `DuplicatePrimaryEnrollment`.
4. Kiểm tra không trùng enrollment cùng lớp → lỗi `EnrollmentAlreadyExists`.
5. Tăng `current_enrollment` của lớp +1.

---

### GET `/classrooms/{class_code}/enrollments`
Danh sách học sinh trong lớp.

**Query params:**
| Param | Type | Mặc định |
|-------|------|---------|
| `page` | int ≥ 1 | 1 |
| `page_size` | int 1–200 | 50 |
| `status` | enum EnrollmentStatus | (tất cả) |

---

### GET `/classrooms/enrollments/{enrollment_id}`
Chi tiết 1 bản ghi enrollment.

---

### PATCH `/classrooms/enrollments/{enrollment_id}`
Cập nhật ghi chú enrollment.

**Body:**
```json
{
  "notes": "Ghi chú mới"
}
```

---

### PATCH `/classrooms/enrollments/{enrollment_id}/status`
Thay đổi trạng thái enrollment.

**Body:**
```json
{
  "new_status": "transferred",
  "left_date": "2026-04-01",
  "notes": "Chuyển sang lớp IELTS Intermediate"
}
```

**Luồng chuyển trạng thái hợp lệ:**
```
active → transferred | withdrawn | completed
transferred → (terminal)
withdrawn → (terminal)
completed → (terminal)
```

> **BE logic khi chuyển khỏi `active`:** Giảm `current_enrollment` của lớp -1.

---

### GET `/classrooms/students/{student_id}/enrollments`
Tất cả lớp mà 1 học sinh đang/đã tham gia.

---

## 8. Grading – Subjects

> **Subject** = Môn học của trung tâm (VD: IELTS, TOEIC, Toán, Lý...).
> 1 lớp học (Classroom) chỉ giảng dạy 1 môn – được xác định qua bảng Class Subjects.

### POST `/grading/subjects`
Tạo môn học.

**Body (required: `*`):**
```json
{
  "subject_code": "IELTS",
  "subject_name": "IELTS Preparation",
  "subject_type": "standard",
  "credits": 4,
  "description": "Khóa luyện thi IELTS"
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
  "subject_name": "IELTS Academic",
  "credits": 5,
  "description": "...",
  "is_active": true
}
```

---

## 9. Grading – Class Subjects (Phân công)

> **Class Subject** = Môn học được phân công dạy tại 1 lớp, 1 học kỳ, bởi 1 giáo viên.
> Đây là đơn vị gốc để nhập điểm và tính lương dạy.
> Vì 1 lớp = 1 môn, thông thường 1 lớp chỉ có 1 Class Subject mỗi học kỳ.

### POST `/grading/class-subjects`
Phân công môn học cho lớp + giáo viên.

**FE gửi (required: `*`):**
```json
{
  "classroom_id": 1,
  "subject_id": 2,
  "teacher_id": 3,
  "semester": 1,
  "academic_year": "2025-2026"
}
```

> **FE cần làm:**
> - `classroom_id`: Dropdown gọi `GET /lookups/classrooms`
> - `subject_id`: Dropdown gọi `GET /lookups/subjects`
> - `teacher_id`: Dropdown gọi `GET /lookups/teachers`
> - Khi chọn classroom, tự động suggest subject nếu lớp đó đã có môn từ kỳ trước

**Logic BE:** Không tạo trùng `(classroom_id, subject_id, semester, academic_year)`.

---

### GET `/grading/class-subjects`
Danh sách phân công môn.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `classroom_id` | int | Lọc theo lớp |
| `teacher_id` | int | Lọc theo giáo viên |
| `subject_id` | int | Lọc theo môn |
| `academic_year` | string | VD: `"2025-2026"` |
| `semester` | int 1–2 | Học kỳ |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–200 | Mặc định: 50 |

---

### GET `/grading/class-subjects/{cs_id}`
Chi tiết phân công môn.

---

### PATCH `/grading/class-subjects/{cs_id}`
Cập nhật phân công (đổi giáo viên, bật/tắt).

**Body:**
```json
{
  "teacher_id": 5,
  "is_active": true
}
```

---

## 10. Grading – Grade Components

> **Grade Component** = Thành phần điểm (kiểm tra miệng, 15 phút, 1 tiết, cuối kỳ...) thuộc 1 Class Subject.
> Mỗi component có trọng số `weight_percent`. Tổng weight nên = 100%.

### POST `/grading/grade-components`
Tạo thành phần điểm.

**Body (required: `*`):**
```json
{
  "class_subject_id": 1,
  "component_name": "Kiểm tra giữa kỳ",
  "weight_percent": 30,
  "min_count": 1
}
```

> **FE cần làm:** Sau khi tạo Class Subject, hiển thị bước "Cấu hình thành phần điểm" ngay. Hiển thị thanh progress tổng weight (0–100%) để người dùng biết còn bao nhiêu % chưa phân bổ.

---

### GET `/grading/grade-components/{class_subject_id}`
Danh sách thành phần điểm của 1 class-subject.

---

### PATCH `/grading/grade-components/{gc_id}`
Cập nhật thành phần điểm.

**Body:** Tất cả optional:
```json
{
  "component_name": "Kiểm tra cuối kỳ",
  "weight_percent": 50,
  "min_count": 1,
  "is_active": true
}
```

---

## 11. Grading – Student Grades

> **Điều kiện trước:** Phải có `class_subject_id` và `grade_component_id` tương ứng, học sinh phải có enrollment active trong lớp đó.

### POST `/grading/grades`
Nhập điểm cho 1 học sinh.

**Body (required: `*`):**
```json
{
  "student_id": 1,
  "class_subject_id": 3,
  "grade_component_id": 2,
  "score": 8.5,
  "exam_date": "2026-04-10",
  "entered_by": 4
}
```

**Logic BE:** Không cho phép nhập trùng `(student_id, class_subject_id, grade_component_id)`.

---

### POST `/grading/grades/bulk`
Nhập điểm hàng loạt (nhiều học sinh, cùng 1 cột điểm). Dùng cho chế độ nhập kiểu Excel.

**Body (required: `*`):**
```json
{
  "class_subject_id": 3,
  "grade_component_id": 2,
  "exam_date": "2026-04-10",
  "entered_by": 4,
  "grades": [
    { "student_id": 1, "score": 8.5 },
    { "student_id": 2, "score": 7.0 },
    { "student_id": 3, "score": 9.0 }
  ]
}
```

> **Logic BE:** Dùng UPSERT (insert nếu chưa có, update nếu đã có). Bọc trong 1 Transaction. Trả về chi tiết từng dòng thành công/thất bại.

---

### GET `/grading/grades/{grade_id}`
Chi tiết 1 bản ghi điểm.

---

### PATCH `/grading/grades/{grade_id}`
Sửa điểm (bắt buộc có lý do – ghi audit log tự động).

**Body (required: `*`):**
```json
{
  "score": 9.0,
  "reason": "Chấm sai, đã phúc tra lại",
  "modified_by": 4
}
```

> **Logic BE:** Mỗi lần sửa tạo 1 bản ghi `GradeAuditLog` lưu điểm cũ, điểm mới, lý do, thời gian.

---

### GET `/grading/grades/{grade_id}/audit-logs`
Lịch sử thay đổi điểm của 1 bản ghi.

---

### GET `/grading/class-subjects/{cs_id}/grades`
Tất cả điểm trong 1 class-subject (dạng danh sách phẳng).

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `grade_component_id` | int | Lọc theo cột điểm |
| `page` | int ≥ 1 | Mặc định: 1 |
| `page_size` | int 1–500 | Mặc định: 100 |

---

### GET `/grading/class-subjects/{cs_id}/grade-matrix` *(BE cần tạo mới)*
**Endpoint mới** – Trả về ma trận điểm dạng Grid (hàng = học sinh, cột = thành phần điểm).

> **FE dùng endpoint này** để render bảng điểm dạng Excel. 1 API call duy nhất load toàn bộ bảng.

**Response data:**
```json
{
  "class_subject_id": 3,
  "classroom_name": "IELTS Basic T2T4",
  "subject_name": "IELTS",
  "semester": 1,
  "academic_year": "2025-2026",
  "components": [
    { "id": 1, "name": "Kiểm tra giữa kỳ", "weight_percent": 30 },
    { "id": 2, "name": "Kiểm tra cuối kỳ", "weight_percent": 50 },
    { "id": 3, "name": "Điểm chuyên cần", "weight_percent": 20 }
  ],
  "students": [
    {
      "student_id": 1,
      "student_code": "Stud2603001",
      "full_name": "Nguyen Van An",
      "grades": {
        "1": { "grade_id": 10, "score": 7.5 },
        "2": { "grade_id": null, "score": null },
        "3": { "grade_id": 15, "score": 9.0 }
      },
      "weighted_average": null
    }
  ]
}
```

> `grades` là object với key = `grade_component_id`. Nếu `grade_id = null` tức chưa nhập điểm.
> `weighted_average` tự tính BE khi đủ điểm tất cả components, hoặc null.

---

## 12. Grading – Reports & Statistics

### GET `/grading/students/{student_id}/report`
Báo cáo điểm học sinh theo học kỳ.

**Query params:**
| Param | Type | Mô tả |
|-------|------|-------|
| `semester` | int 1–2 | Lọc theo học kỳ |
| `academic_year` | string | VD: `"2025-2026"` |

**Response data:**
```json
{
  "student_id": 1,
  "student_code": "Stud2603001",
  "full_name": "Nguyen Van An",
  "semester": 1,
  "academic_year": "2025-2026",
  "subjects": [
    {
      "class_subject_id": 3,
      "subject_name": "IELTS",
      "classroom_name": "IELTS Basic T2T4",
      "components": [...],
      "semester_average": 8.1
    }
  ],
  "overall_average": 8.1,
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
  "classroom_name": "IELTS Basic T2T4",
  "subject_name": "IELTS",
  "semester": 1,
  "academic_year": "2025-2026",
  "total_students": 20,
  "graded_students": 18,
  "avg_score": 7.5,
  "max_score": 10.0,
  "min_score": 3.5,
  "rank_distribution": {
    "Gioi": 5,
    "Kha": 8,
    "TrungBinh": 4,
    "Yeu": 1
  }
}
```

---

## 13. Salary – Salary Grades

> **Salary Grade** = Ngạch lương, định nghĩa mức lương cơ bản và đơn giá tiết dạy theo trình độ + thâm niên.

### POST `/salary/grades`
Tạo ngạch lương.

**Body (required: `*`):**
```json
{
  "grade_code": "THAC_SI_3_6NAM",
  "qualification_level": "thac_si",
  "experience_tier": "3_to_6y",
  "base_salary": 8500000,
  "hourly_rate": 85000,
  "effective_from": "2026-01-01",
  "effective_to": null,
  "description": "Thạc sĩ, 3–6 năm kinh nghiệm"
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
  "effective_to": "2026-12-31",
  "description": "...",
  "is_active": false
}
```

---

## 14. Salary – Bonus Policies

> **Bonus Policy** = Chính sách thưởng tái sử dụng (thưởng thâm niên, thưởng GVCN...).

### POST `/salary/bonus-policies`
Tạo chính sách thưởng.

**Body (required: `*`):**
```json
{
  "policy_code": "THUONG_THAM_NIEN_3NAM",
  "policy_name": "Thưởng đạt mốc 3 năm",
  "bonus_type": "fixed",
  "bonus_value": 500000,
  "condition_description": "Áp dụng cho GV đủ 3 năm công tác"
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

## 15. Salary – Payrolls

> **Payroll** = Bảng lương tháng của 1 giáo viên. Trải qua 3 trạng thái: `draft → confirmed → paid`.

### POST `/salary/payrolls`
Tạo bảng lương tháng.

**FE gửi (required: `*`):**
```json
{
  "teacher_id": 1,
  "salary_grade_id": 2,
  "payroll_month": "2026-03-01",
  "work_days_standard": 22,
  "work_days_actual": 21,
  "teaching_hours_standard": 80,
  "teaching_hours_actual": 90,
  "base_salary": 8500000,
  "teaching_allowance": 850000,
  "deductions": 0,
  "notes": "...",
  "bonus_details": [
    {
      "bonus_policy_id": 1,
      "amount": 500000,
      "note": "Thưởng thâm niên 3 năm"
    }
  ]
}
```

> **FE cần làm:**
> - `teacher_id`: Dropdown gọi `GET /lookups/teachers`
> - `salary_grade_id`: Dropdown gọi `GET /salary/grades?active_only=true` (hiển thị tên ngạch lương)
> - Tự tính preview `net_salary = base_salary + teaching_allowance + sum(bonus_details.amount) - deductions` để người dùng thấy trước khi submit
> - `bonus_details`: Danh sách động (thêm/xóa khoản thưởng), mỗi khoản là Dropdown chọn từ Bonus Policies

> **BE logic:** `net_salary` = `base_salary + teaching_allowance + total_bonus - deductions`. Tính lại khi tạo/cập nhật.

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
Cập nhật bảng lương (chỉ cho phép khi `status = draft`).

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
  "new_status": "confirmed",
  "confirmed_by": 5,
  "notes": "Đã kiểm tra, duyệt chi"
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
  "bonus_policy_id": 1,
  "amount": 500000,
  "note": "Thưởng GVCN tháng 3"
}
```

> **Logic BE:** Sau khi thêm bonus, `total_bonus` và `net_salary` được tính lại tự động.

---

## 16. Enums Reference

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
| `primary` | Lớp chính (mỗi HS chỉ có 1 tại 1 thời điểm) |
| `secondary` | Lớp phụ / bổ sung |

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

## 17. Business Logic & Luồng xử lý đầy đủ

### Luồng 1: Tạo học sinh & xếp lớp (tích hợp)

```
[FE] Mở form "Thêm học sinh"
  └─ KHÔNG có ô "Mã học sinh" (BE tự sinh)
  └─ Điền thông tin cá nhân + phụ huynh
  └─ Chọn lớp (Multi-select Dropdown từ GET /lookups/classrooms) → OPTIONAL

[FE] Submit → POST /api/v1/students
  Body: { full_name, ..., class_ids: [1, 5] }

[BE] Nhận request:
  1. Sinh mã: query MAX student_code tháng hiện tại → tạo Stud2603xxx
  2. INSERT students (flush để lấy ID)
  3. Nếu có class_ids:
     - FOR EACH class_id: SELECT classroom WITH FOR UPDATE
     - Nếu đầy: ghi { classroom_id, status: "failed", reason: "..." } vào result
     - Nếu OK: INSERT enrollment, UPDATE current_enrollment +1
  4. COMMIT transaction
  5. Trả về student + enrollment results

[FE] Nhận response:
  - Hiển thị toast "Tạo học sinh thành công – Mã: Stud2603001"
  - Nếu có lớp failed: hiển thị warning "Không thể xếp vào lớp TOEIC 650: Lớp đã đầy"
```

---

### Luồng 2: Xếp lớp cho học sinh đang chờ

```
[FE] Màn hình danh sách HS → Filter "Chờ xếp lớp" (has_enrollment=false)
[FE] Click icon "Xếp lớp" ở dòng HS → Mở modal
  └─ Combobox tìm lớp (GET /lookups/classrooms?has_capacity=true)
  └─ Chọn loại đăng ký (primary / secondary)

[FE] Submit → POST /api/v1/classrooms/{class_code}/enrollments
  Body: { student_id, enrollment_type, enrolled_date }

[BE] Kiểm tra capacity → tạo enrollment → cập nhật current_enrollment
[FE] Refetch danh sách, HS biến mất khỏi filter "Chờ xếp lớp"
```

---

### Luồng 3: Nhập điểm cho lớp (chế độ Grid/Excel)

```
[FE] Màn hình "Bảng điểm" → Chọn lớp học → Chọn học kỳ
  └─ Gọi GET /grading/class-subjects?classroom_id=1&semester=1
  └─ Lấy cs_id → Gọi GET /grading/class-subjects/{cs_id}/grade-matrix

[BE] Trả về ma trận: danh sách HS × danh sách components × điểm hiện tại

[FE] Render bảng dạng Grid:
  - Hàng = học sinh (student_code + full_name)
  - Cột = thành phần điểm (kiểm tra giữa kỳ, cuối kỳ, chuyên cần...)
  - Ô có điểm: hiển thị số, click để sửa (highlight màu)
  - Ô chưa có điểm: ô trống, click để nhập

[FE] Người dùng nhập/sửa nhiều ô → bấm "Lưu tất cả":
  → POST /grading/grades/bulk (nhập mới)
  → PATCH /grading/grades/{grade_id} với reason (khi sửa điểm đã có)

[BE] Bulk insert/update trong 1 Transaction. Trả về kết quả từng dòng.
```

---

### Luồng 4: Phân công giảng dạy & cấu hình điểm (setup đầu kỳ)

```
1. Tạo Subject (nếu chưa có)   POST /grading/subjects
2. Tạo Classroom               POST /classrooms
3. Phân công dạy               POST /grading/class-subjects
      └─ classroom_id (Dropdown) + subject_id (Dropdown) + teacher_id (Dropdown)
4. Cấu hình thành phần điểm   POST /grading/grade-components (lặp cho từng thành phần)
      └─ FE hiển thị progress bar tổng weight, đạt 100% mới cho lưu
5. Enroll học sinh             POST /classrooms/{class_code}/enrollments (từng HS)
      └─ Hoặc tạo HS mới với class_ids để enroll hàng loạt
6. Nhập điểm khi có kết quả   POST /grading/grades/bulk
7. Xem báo cáo                 GET /grading/students/{student_id}/report
                               GET /grading/class-subjects/{cs_id}/statistics
```

---

### Luồng 5: Tính lương giáo viên tháng

```
1. Kiểm tra / tạo Salary Grade POST /salary/grades (nếu ngạch lương chưa có)
2. Tạo Payroll tháng           POST /salary/payrolls
      └─ teacher_id (Dropdown) + salary_grade_id (Dropdown)
      └─ Nhập giờ dạy thực tế, khấu trừ, bonus (thêm động)
      └─ FE hiển thị preview net_salary realtime
3. Duyệt payroll               PATCH /salary/payrolls/{id}/status { "new_status": "confirmed" }
4. Thanh toán                  PATCH /salary/payrolls/{id}/status { "new_status": "paid" }
```

---

### Ràng buộc quan trọng

| Ràng buộc | Mô tả |
|-----------|-------|
| `student_code`, `teacher_code` | Auto-generated by BE – format `StudYYMMxxx` / `TchrYYMMxxx` |
| `class_code`, `subject_code` | Unique trong toàn hệ thống |
| `email`, `national_id` (student/teacher) | Unique nếu có giá trị (dùng Filtered Index cho NULL ở MSSQL) |
| Enrollment PRIMARY | Mỗi học sinh chỉ được có 1 lớp primary active tại 1 thời điểm |
| Enrollment capacity | Không thể enroll khi `current_enrollment >= max_capacity` |
| Grade unique | `(student_id, class_subject_id, grade_component_id)` unique |
| Grade audit | Mọi thao tác sửa điểm (`PATCH /grades/{id}`) đều bắt buộc `reason` và tạo audit log |
| Payroll editable | Chỉ cập nhật/thêm bonus khi `status != paid` |
| Status transition | Mọi chuyển trạng thái đều có whitelist hợp lệ ở cả FE lẫn BE |
| Soft-delete | Không xóa cứng bất kỳ record nào – chỉ set `is_active = false` |
| Race condition (enrollment) | BE dùng `SELECT ... FOR UPDATE` (row lock) khi kiểm tra capacity |

---

### Tóm tắt các việc cần làm ngay (Priority)

#### BE – Cần tạo/sửa
| # | Việc cần làm | Độ ưu tiên |
|---|-------------|-----------|
| 1 | Bỏ `student_code` & `teacher_code` khỏi request body. Tự sinh theo format mới | 🔴 Cao |
| 2 | Tích hợp `class_ids` vào `POST /students` (tạo HS + enroll 1 transaction) | 🔴 Cao |
| 3 | Tạo các `GET /lookups/...` (teachers, classrooms, students, subjects) | 🔴 Cao |
| 4 | Thêm filter `has_enrollment` và `classroom_id` vào `GET /students` | 🟡 Trung bình |
| 5 | Bổ sung `current_enrollments` vào response `GET /students/{code}` | 🟡 Trung bình |
| 6 | Bổ sung `teaching_assignments` vào response `GET /teachers/{code}` | 🟡 Trung bình |
| 7 | Tạo endpoint `GET /grading/class-subjects/{cs_id}/grade-matrix` | 🔴 Cao |
| 8 | Sửa `POST /grading/grades/bulk` thành UPSERT | 🟡 Trung bình |
| 9 | Thêm `pending_enrollment_students` vào `GET /dashboard/stats` | 🟢 Thấp |
| 10 | Thêm filter `has_capacity` vào `GET /classrooms` | 🟢 Thấp |

#### FE – Cần tạo/sửa
| # | Việc cần làm | Độ ưu tiên |
|---|-------------|-----------|
| 1 | Xóa field `student_code` khỏi `StudentForm` & Zod schema | 🔴 Cao |
| 2 | Xóa field `teacher_code` khỏi `TeacherForm` & Zod schema | 🔴 Cao |
| 3 | Đổi "ID học sinh" trong `EnrollmentDialog` từ Input số → Combobox search | 🔴 Cao |
| 4 | Thêm `class_ids` Multi-select vào `StudentForm` (gọi `/lookups/classrooms`) | 🔴 Cao |
| 5 | Đổi `homeroom_teacher_id` trong `ClassroomForm` từ Input → Dropdown (gọi `/lookups/teachers`) | 🟡 Trung bình |
| 6 | Thêm filter "Chờ xếp lớp" (`has_enrollment=false`) ở `StudentsPage` | 🟡 Trung bình |
| 7 | Xây dựng `GradeMatrixTable` component (bảng điểm dạng Grid/Excel) | 🔴 Cao |
| 8 | Thêm preview `net_salary` realtime ở form tạo Payroll | 🟢 Thấp |
| 9 | Hiển thị tab "Lớp đang học" trong detail HS, "Phân công dạy" trong detail GV | 🟡 Trung bình |
