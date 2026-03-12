# KẾ HOẠCH PHÁT TRIỂN HỆ THỐNG QUẢN LÝ GIÁO DỤC (EMS)

## 1. Phân tích chi tiết các Module Tính năng
*(Bao quát các trường hợp (Edge cases) và luồng nghiệp vụ cơ bản)*

### 1.1. Module Quản lý Học sinh / Sinh viên (Priority - Ưu tiên cao)
* **Quản lý Hồ sơ (Profile Management):** Nhập/xuất danh sách học sinh (Excel/CSV), lưu trữ thông tin cá nhân, liên hệ phụ huynh, lịch sử y tế, trạng thái học tập (đang học, bảo lưu, đình chỉ, đã tốt nghiệp).
* **Quản lý Học vụ (Academic Management):** Đăng ký môn học/khóa học, xếp lớp, quản lý điểm số (điểm thành phần, điểm thi, tính điểm trung bình), quản lý điểm danh (chuyên cần, nghỉ phép có/không phép).
* **Quản lý Tài chính (Financial Management):** Theo dõi học phí, các khoản thu hộ/chi hộ, miễn giảm học phí (học bổng), nhắc nhở nợ đọng, xuất biên lai (PDF).
* **Trường hợp phát sinh (Edge cases):** * Học sinh chuyển lớp giữa kỳ.
    * Bảo lưu rồi quay lại học nhưng chương trình học cũ đã thay đổi.
    * Sai sót điểm cần quy trình xin sửa điểm và lưu lại lịch sử chỉnh sửa (Audit log - ai sửa, sửa khi nào, từ điểm mấy thành điểm mấy).

### 1.2. Module Quản lý Giáo viên (Priority - Ưu tiên cốt lõi / Điểm "Ăn Tiền")
* **Quản lý Nhân sự:** Hồ sơ cá nhân, bằng cấp, chứng chỉ, hợp đồng lao động, thâm niên giảng dạy.
* **Quản lý Phân công & Lịch trình:** Phân công lớp dạy, theo dõi thời khóa biểu (tránh trùng lịch giữa các lớp hoặc trùng với thời gian nghỉ của giáo viên). Quản lý luồng dạy thay, dạy bù linh hoạt.
* **Đánh giá, Chấm công & Tính lương (Tính năng cốt lõi):** * *Cơ chế tự chấm công:* Tích hợp QR Code động (Dynamic QR sinh ra trên app của giáo viên/màn hình lớp học) hoặc xác thực vị trí (Geolocation) để giáo viên tự quét mã check-in/check-out khi đến lớp.
    * *Ghi nhận & Đánh giá:* Ghi nhận số tiết dạy thực tế, đánh giá hiệu suất (từ form feedback của học sinh hoặc KPI phòng đào tạo). Quản lý ngày phép (có lương/không lương).
    * *Module Lương/Thưởng:* Hệ thống tự động map dữ liệu chấm công + ngạch bậc lương + số tiết thực dạy + thưởng KPI để xuất ra bảng lương tạm tính theo tháng/quý. Hỗ trợ kế toán chốt lương chỉ với 1 click.
* **Trường hợp phát sinh (Edge cases):** * Giáo viên nghỉ đột xuất: Hệ thống tự động filter và *gợi ý người dạy thay* đáp ứng đủ 2 tiêu chí: Có cùng chuyên môn môn học VÀ đang trống lịch vào khung giờ đó.
    * *Tính năng Availability Tracking:* Cho phép giáo viên tự đăng nhập và đăng ký/lưu "thời gian rảnh" (Free time slots) trong tuần để phòng đào tạo dễ dàng chủ động xếp lịch phụ đạo hoặc dạy thay mà không cần gọi điện hỏi từng người.

### 1.3. Module Quản lý Cơ sở vật chất (Least Need - Mức độ ưu tiên thấp)
* **Quản lý Danh mục (Inventory):** Quản lý phòng học, trang thiết bị (máy chiếu, máy tính, bàn ghế), phân loại tài sản theo tình trạng (mới, đang sử dụng, hỏng, đang bảo trì).
* **Quản lý Đặt mượn (Booking & Allocation):** Hệ thống đặt phòng học cho các sự kiện/lớp học phụ đạo, mượn trả thiết bị (tránh trùng lặp thời gian).
* **Bảo trì & Khấu hao:** Lên lịch bảo trì định kỳ, ghi nhận chi phí sửa chữa, tính khấu hao tài sản theo thời gian.
* **Trường hợp phát sinh:** Đặt phòng trùng lặp do thao tác đồng thời (Concurrency issue), thiết bị hỏng đột xuất cần báo cáo và điều chuyển phòng ngay lập tức.

---

## 2. Kiến trúc Hệ thống (System Architecture)

### 2.1. Front-end (UI/UX & AI Assisted)
* **Định hướng công nghệ:** Sử dụng **Next.js** (cấu trúc thư mục tốt, hỗ trợ SEO nếu cần, dễ tối ưu và render nhanh).
* **Quy trình phát triển:** Sử dụng **AI Vibe Coding**. Sử dụng GitHub Copilot (hoặc Cursor IDE) để thực hiện các bước phát triển theo quy trình. Developer đóng vai trò định hướng prompt, AI sẽ gen ra các component UI nhanh chóng.
* **Tương tác:** Giao tiếp với Back-end độc lập hoàn toàn thông qua RESTful API.

### 2.2. Back-end (Server chính)
* **Công nghệ:** **Python** kết hợp với framework **FastAPI** (khuyến nghị số 1 vì tốc độ cực cao, hỗ trợ bất đồng bộ `async/await` nguyên bản, tự động sinh tài liệu Swagger UI/Redoc cực kỳ tiện cho Front-end đọc API).
* **Nhiệm vụ:** Xử lý logic nghiệp vụ, xác thực người dùng (JWT/OAuth2), phân quyền (Role-based access control - RBAC: Admin, Giáo viên, Kế toán, Học sinh).

### 2.3. Cơ sở dữ liệu (Database) & Caching
* **Main DB (MSSQL):** Đảm bảo tính toàn vẹn dữ liệu (ACID) cho các giao dịch quan trọng (điểm số, tài chính lương bổng). Sử dụng **SQLAlchemy** (ORM chuẩn mực nhất của Python) để tương tác.
* **Cache (Redis):** * Lưu trữ Session người dùng / Blacklist JWT Token.
    * Cache các dữ liệu ít thay đổi nhưng được truy vấn liên tục (Danh sách môn học, thời khóa biểu tĩnh, danh mục cơ sở vật chất) để giảm tải cho MSSQL.

---

## 3. Khả năng chịu tải & Tối ưu hóa (Scale & Optimization)
*(Mục tiêu: ~100 concurrent users. Đây là mức tải nhỏ - trung bình, hệ thống xử lý mượt mà nếu tối ưu tốt)*

### 3.1. Tiếp cận máy chủ (Hosting / Server)
* **Cấu hình đề xuất:** 1 VPS có 4 vCPU, 8GB RAM, 100GB SSD (AWS EC2, DigitalOcean, hoặc VPS VN để tối ưu ping).
* **Web Server:** Sử dụng **Nginx** làm Reverse Proxy, kết hợp với **Gunicorn** quản lý các worker **Uvicorn** để chạy ứng dụng FastAPI.

### 3.2. Chiến lược Tối ưu hóa (Optimization)
* **Database Indexing:** Tạo Index cho các cột thường xuyên được tìm kiếm trong MSSQL. *Lưu ý: Bắt buộc dùng tên biến tiếng Anh cho DB Schema (VD: `student_code`, `full_name`, `phone_number`).*
* **Connection Pooling:** Cấu hình pool kết nối tới MSSQL thông qua SQLAlchemy (cấu hình `pool_size`, `max_overflow`) để tái sử dụng connection.
* **Tối ưu truy vấn (N+1 Query Problem):** Tránh việc query vào database trong các vòng lặp. Sử dụng tính năng `JOIN` hoặc *eager loading* (như `joinedload` trong SQLAlchemy).
* **Redis Caching:** Áp dụng cache cho các Dashboard tổng quan. Thực hiện cập nhật cache (Cache Invalidation) chuẩn xác mỗi khi có thay đổi (Create/Update/Delete).

---

## 4. Kế hoạch Backup Dữ liệu (Future Plan)
*Áp dụng quy tắc backup 3-2-1:*
* **Cấp độ Database (MSSQL):**
    * *Full Backup:* Tự động chạy vào 2h sáng Chủ Nhật hàng tuần.
    * *Differential Backup:* Chạy mỗi ngày một lần vào 2h sáng các ngày còn lại.
    * *Transaction Log Backup:* Cứ mỗi 1 - 2 tiếng/lần để tránh mất dữ liệu tài chính/điểm số.
* **Cấp độ File/Media:** Sao lưu các file đính kèm định kỳ mỗi ngày.
* **Nơi lưu trữ:** Cloud Storage (AWS S3, Google Cloud Storage) hoặc một máy chủ vật lý khác vị trí địa lý.

---

## 5. Kế hoạch Kiểm thử Phần mềm (Least Need - Mức độ ưu tiên thấp)
* **Unit Testing (Back-end):** Dùng `pytest` (Python) test logic lõi (tính điểm trung bình, lương giáo viên).
* **Integration Testing:** Kiểm tra luồng dữ liệu API -> Database -> Cache.
* **User Acceptance Testing (UAT):** Người dùng cuối (giáo vụ, giáo viên) dùng thử giao diện.
* **Load Testing:** Dùng `Locust` (viết bằng Python) giả lập 150-200 user đăng nhập/tra điểm cùng lúc.

---

## 6. Quy hoạch Tiêu chuẩn Code, Cấu trúc Thư mục & Bắt lỗi (Architecture & Standard Pattern)

### 6.1. Quy tắc đặt tên biến (Naming Convention)
* **Đồng nhất & Tiếng Anh:** Toàn bộ hệ thống dùng tiếng Anh. Tên biến phải đủ nghĩa, **tuyệt đối không viết tắt** (VD: dùng `student_registration_date` thay vì `stu_reg_dt`).
* **Không duplicate ngữ nghĩa:** Phân tách rõ ràng vai trò (VD: `host` - người tạo phòng, `celebrater` - người tổ chức, `manager` - quản lý chung, `admin` - quản trị hệ thống).

### 6.2. Tổ chức Structure (Clean Architecture Pattern)
Back-end FastAPI sẽ được chia theo cấu trúc các module (domains) chuyên biệt. Trong mỗi module sẽ có luồng chảy (Flow) một chiều chuẩn:

* **`Entity` (Models):** Nơi định nghĩa Schema Database. Chứa các class map trực tiếp với các bảng trong MSSQL (dùng SQLAlchemy Models).
* **`DTO` (Data Transfer Object / Schemas):** Nơi "hứng", validate và định dạng dữ liệu đầu vào/đầu ra từ API (Dùng Pydantic của FastAPI). Tại đây có thể map/đổi tên biến từ Client gửi lên về đúng chuẩn tên Entity.
* **`Repository`:** Lớp giao tiếp trực tiếp với DB. Nơi thực thi các lệnh query phức tạp (CRUD, JOIN). Service sẽ gọi Repository chứ không gọi DB trực tiếp.
* **`Service`:** "Trái tim" của hệ thống. Nơi chứa business logic thực tế (tính lương, xếp lớp, scheduling tự động như báo lịch học, báo nghỉ qua Celery/APScheduler).
* **`Controller` (Routers):** Nơi định nghĩa các endpoint API (`@app.get`, `@app.post`). Nhiệm vụ duy nhất là nhận request, gọi đến `Service` tương ứng, và trả về response.

### 6.3. Tiêu chuẩn Response API hiện đại
Mọi API trả về (dù thành công hay thất bại) đều phải tuân theo một JSON format duy nhất, giúp Front-end dễ dàng parse dữ liệu:
```json
{
  "code": 200,
  "message": "Success",
  "detail": "Retrieved student list successfully",
  "data": { ... }
}
```

---

## 7. Database Schema – Thiết kế Thực thể Mới (Plan – chờ approve)

> Phần này mô tả các bảng sẽ được tạo mới. Sau khi được approve, sẽ tạo entity/dto/repository/service/controller cho từng module.

---

### 7.1. Module Quản lý Lớp học (`classroom`)

#### Bảng `classrooms` – Thông tin lớp
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | Auto-increment |
| `class_code` | VARCHAR(20) UNIQUE | Mã lớp, VD: `10A1-2024` |
| `class_name` | NVARCHAR(100) | Tên hiển thị, VD: `Lớp 10A1` |
| `class_type` | ENUM | `standard` – Lớp cơ bản / `cambridge` – Lớp nâng cao Cambridge |
| `academic_year` | VARCHAR(10) | Năm học, VD: `2024-2025` |
| `grade_level` | INT | Khối lớp: 10 / 11 / 12 |
| `homeroom_teacher_id` | INT FK → teachers | Giáo viên chủ nhiệm |
| `max_capacity` | INT | Sĩ số tối đa |
| `current_enrollment` | INT | Sĩ số hiện tại (tự tính) |
| `room_number` | VARCHAR(20) | Phòng học |
| `is_active` | BIT | Soft-delete |
| `created_at` / `updated_at` | DATETIME | Auto timestamp |

**Nghiệp vụ phân cấp lớp:**
- `class_type = standard`: Lớp cơ bản theo chương trình Bộ GD&ĐT
- `class_type = cambridge`: Lớp nâng cao theo chuẩn Cambridge International
- Học sinh lớp `standard` **có thể** đăng ký học thêm lớp `cambridge` (cross-enrollment)
- Học sinh lớp `cambridge` **có thể** theo dõi chương trình `standard` song song

#### Bảng `student_class_enrollments` – Học sinh đăng ký lớp
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `student_id` | INT FK → students | |
| `classroom_id` | INT FK → classrooms | |
| `enrollment_type` | ENUM | `primary` – lớp chính / `supplementary` – lớp học thêm (cross-enrollment) |
| `enrolled_date` | DATE | Ngày vào lớp |
| `left_date` | DATE | Ngày rời lớp (NULL = đang học) |
| `is_active` | BIT | Soft flag |

> **Rule cross-enrollment:** Một học sinh có đúng 1 enrollment `primary` tại một thời điểm. Số lượng `supplementary` không giới hạn nhưng giới hạn bởi `max_capacity` của lớp đó.

---

### 7.2. Module Tính lương Giáo viên (`payroll`)

#### Bảng `salary_grades` – Bảng ngạch lương
Ngạch lương được xác định bởi **tổ hợp** (bằng cấp × mốc thâm niên):

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `grade_code` | VARCHAR(20) UNIQUE | VD: `THAC_SI_3NAM` |
| `qualification_level` | ENUM | `cao_dang` / `dai_hoc` / `thac_si` / `tien_si` |
| `experience_tier` | ENUM | `under_3y` / `3_to_6y` / `6_to_9y` / `over_9y` |
| `base_salary` | DECIMAL(15,2) | Mức lương cơ bản (VNĐ/tháng) |
| `hourly_rate` | DECIMAL(10,2) | Đơn giá/tiết dạy (dùng để tính lương theo số tiết) |
| `effective_from` | DATE | Áp dụng từ ngày |
| `effective_to` | DATE | Hết hiệu lực (NULL = đang áp dụng) |

**Ví dụ bảng ngạch:**
| Bằng cấp | < 3 năm | 3–6 năm | 6–9 năm | > 9 năm |
|----------|---------|---------|---------|---------|
| Cao đẳng | 7.5M | 8.5M | 9.5M | 10.5M |
| Đại học | 9M | 10.5M | 12M | 13.5M |
| Thạc sĩ | 11M | 13M | 15M | 17M |
| Tiến sĩ | 14M | 16.5M | 19M | 22M |

#### Bảng `bonus_policies` – Chính sách thưởng
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `policy_code` | VARCHAR(30) UNIQUE | VD: `THUONG_GIANG_DAY_XUAT_SAC` |
| `policy_name` | NVARCHAR(200) | Tên chính sách |
| `bonus_type` | ENUM | `fixed` – số tiền cố định / `percentage` – % lương cơ bản |
| `bonus_value` | DECIMAL(15,2) | Giá trị (VNĐ hoặc %) |
| `condition_description` | NVARCHAR(500) | Mô tả điều kiện áp dụng |
| `is_active` | BIT | |

**Các loại thưởng dự kiến:**
- Thưởng thâm niên đạt mốc 3/6/9 năm (fixed)
- Thưởng cuối năm theo xếp loại KPI (percentage: Xuất sắc 150%, Tốt 100%, Khá 50%)
- Thưởng lớp đạt tỷ lệ pass Cambridge (fixed)
- Thưởng giảng dạy ngoài giờ / dạy thêm (theo tiết)

#### Bảng `monthly_payroll` – Bảng lương tháng
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `teacher_id` | INT FK → teachers | |
| `salary_grade_id` | INT FK → salary_grades | Ngạch lương áp dụng tháng này |
| `payroll_month` | DATE | Tháng lương (lưu ngày 1 của tháng) |
| `work_days_standard` | INT | Số ngày công chuẩn (VD: 22) |
| `work_days_actual` | INT | Số ngày thực tế có mặt |
| `teaching_hours_standard` | INT | Số tiết chuẩn theo hợp đồng |
| `teaching_hours_actual` | INT | Số tiết thực dạy trong tháng |
| `base_salary` | DECIMAL(15,2) | Lương cơ bản từ ngạch |
| `teaching_allowance` | DECIMAL(15,2) | Phụ cấp tiết dạy vượt chuẩn |
| `total_bonus` | DECIMAL(15,2) | Tổng thưởng tháng này |
| `deductions` | DECIMAL(15,2) | Khấu trừ (nghỉ không phép, BHXH...) |
| `net_salary` | DECIMAL(15,2) | Thực lãnh = base + allowance + bonus - deductions |
| `status` | ENUM | `draft` / `confirmed` / `paid` |
| `confirmed_by` | INT FK → users | Kế toán duyệt |
| `confirmed_at` | DATETIME | |
| `notes` | NVARCHAR(500) | |

#### Bảng `payroll_bonus_details` – Chi tiết các khoản thưởng trong 1 bảng lương
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `payroll_id` | INT FK → monthly_payroll | |
| `bonus_policy_id` | INT FK → bonus_policies | |
| `amount` | DECIMAL(15,2) | Số tiền thưởng thực tế |
| `note` | NVARCHAR(300) | |

---

### 7.3. Module Điểm số & Thống kê (`grading`)

#### Bảng `subjects` – Môn học
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `subject_code` | VARCHAR(20) UNIQUE | VD: `TOAN`, `VAN`, `CAM_MATH` |
| `subject_name` | NVARCHAR(100) | |
| `subject_type` | ENUM | `standard` / `cambridge` |
| `credits` | INT | Số tín chỉ / hệ số |
| `is_active` | BIT | |

#### Bảng `class_subjects` – Phân công môn học – lớp – giáo viên
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `classroom_id` | INT FK → classrooms | |
| `subject_id` | INT FK → subjects | |
| `teacher_id` | INT FK → teachers | Giáo viên phụ trách môn này tại lớp này |
| `semester` | INT | Học kỳ: 1 / 2 |
| `academic_year` | VARCHAR(10) | |

#### Bảng `grade_components` – Cấu hình thành phần điểm
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `class_subject_id` | INT FK → class_subjects | |
| `component_name` | NVARCHAR(100) | VD: `Kiểm tra miệng`, `15 phút`, `1 tiết`, `Cuối kỳ` |
| `weight_percent` | INT | Hệ số %, tổng các thành phần = 100 |
| `min_count` | INT | Số cột tối thiểu bắt buộc |

#### Bảng `student_grades` – Điểm từng học sinh
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `student_id` | INT FK → students | |
| `class_subject_id` | INT FK → class_subjects | |
| `grade_component_id` | INT FK → grade_components | Loại điểm |
| `score` | DECIMAL(4,2) | 0.00 – 10.00 |
| `exam_date` | DATE | Ngày kiểm tra |
| `entered_by` | INT FK → teachers | Giáo viên nhập điểm |
| `entered_at` | DATETIME | |
| `last_modified_by` | INT FK → teachers | Người sửa điểm (audit) |
| `last_modified_at` | DATETIME | |
| `is_active` | BIT | Soft-delete (dùng khi hủy điểm sai) |

#### Bảng `grade_audit_log` – Lịch sử sửa điểm
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `student_grade_id` | INT FK → student_grades | |
| `old_score` | DECIMAL(4,2) | Điểm cũ |
| `new_score` | DECIMAL(4,2) | Điểm mới |
| `changed_by` | INT FK → teachers | |
| `changed_at` | DATETIME | |
| `reason` | NVARCHAR(300) | Lý do chỉnh sửa (bắt buộc) |

#### Bảng `semester_averages` – Điểm trung bình học kỳ (materialized)
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | INT PK | |
| `student_id` | INT FK → students | |
| `class_subject_id` | INT FK → class_subjects | |
| `semester` | INT | |
| `academic_year` | VARCHAR(10) | |
| `average_score` | DECIMAL(4,2) | Tính từ student_grades + weight |
| `rank` | NVARCHAR(20) | `Gioi` / `Kha` / `Trung binh` / `Yeu` |
| `calculated_at` | DATETIME | Lần tính gần nhất |

---

## 8. Sơ đồ quan hệ tổng thể (ERD tóm tắt)

```
teachers ──┬── class_subjects ──── classrooms ──── student_class_enrollments ──── students
           │         │                                                                │
           │    grade_components                                                      │
           │         │                                                                │
           └── student_grades ────────────────────────────────────────────────────────┘
                     │
               grade_audit_log

teachers ──── monthly_payroll ──── payroll_bonus_details ──── bonus_policies
                    │
              salary_grades
```

---

## 9. Thứ tự triển khai (Implementation Roadmap)

| Bước | Module | File cần tạo | Ghi chú |
|------|--------|-------------|---------|
| **1** | **Auth** | `user/entity`, `user/dto`, `user/repository`, `user/service`, `user/controller`, `core/security.py`, `core/dependencies.py` | Bắt buộc trước, tất cả module sau cần auth |
| **2** | **Classroom** | `classroom/entity`, `classroom/dto`, `classroom/repository`, `classroom/service`, `classroom/controller` | Entity `classrooms` + `student_class_enrollments` |
| **3** | **Subject + Class Assignment** | `subject/entity`, `subject/dto`, ... | Entity `subjects` + `class_subjects` + `grade_components` |
| **4** | **Grading** | `grading/entity`, `grading/dto`, `grading/repository`, `grading/service`, `grading/controller` | Nhập điểm, audit log, tính trung bình, báo cáo/biểu đồ |
| **5** | **Salary** | `salary/entity`, `salary/dto`, `salary/repository`, `salary/service`, `salary/controller` | Ngạch lương, bảng lương tháng, thưởng |
| **6** | Tests | `tests/test_student.py`, `tests/test_teacher.py`, ... | Unit + integration |

---

## 10. API Endpoints dự kiến (tóm tắt)

```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout

GET    /api/v1/classrooms
POST   /api/v1/classrooms
GET    /api/v1/classrooms/{class_code}
PATCH  /api/v1/classrooms/{class_code}
DELETE /api/v1/classrooms/{class_code}
POST   /api/v1/classrooms/{class_code}/enroll          # Xếp học sinh vào lớp
DELETE /api/v1/classrooms/{class_code}/enroll/{student_code}

GET    /api/v1/subjects
POST   /api/v1/subjects

GET    /api/v1/grading/classes/{class_code}/subjects/{subject_code}   # Bảng điểm lớp
POST   /api/v1/grading/enter                                           # Nhập điểm (teacher only)
PATCH  /api/v1/grading/{grade_id}                                      # Sửa điểm (có audit)
GET    /api/v1/grading/students/{student_code}/report                  # Báo cáo điểm học sinh
GET    /api/v1/grading/classes/{class_code}/statistics                 # Thống kê/biểu đồ lớp

GET    /api/v1/salary/grades                           # Bảng ngạch lương
POST   /api/v1/salary/payroll/generate                 # Tạo bảng lương tháng (auto-calc)
GET    /api/v1/salary/payroll/{teacher_code}/{month}   # Xem bảng lương
PATCH  /api/v1/salary/payroll/{id}/confirm             # Kế toán duyệt
GET    /api/v1/salary/payroll/export/{month}           # Xuất Excel tất cả giáo viên
```

---

## Endpoints hiện tại

| Method | URL | Mô tả |
|--------|-----|-------|
| GET | `/health` | Kiểm tra kết nối DB |
| GET | `/docs` | Swagger UI |
| POST | `/api/v1/students` | Tạo học sinh |
| GET | `/api/v1/students` | Danh sách học sinh |
| GET | `/api/v1/students/{student_code}` | Chi tiết học sinh |
| PATCH | `/api/v1/students/{student_code}` | Cập nhật học sinh |
| PATCH | `/api/v1/students/{student_code}/status` | Đổi trạng thái |
| DELETE | `/api/v1/students/{student_code}` | Xóa mềm |
| POST | `/api/v1/teachers` | Tạo giáo viên |
| GET | `/api/v1/teachers` | Danh sách giáo viên |
| GET | `/api/v1/teachers/{teacher_code}` | Chi tiết giáo viên |
| PATCH | `/api/v1/teachers/{teacher_code}` | Cập nhật giáo viên |
| PATCH | `/api/v1/teachers/{teacher_code}/status` | Đổi trạng thái |
| DELETE | `/api/v1/teachers/{teacher_code}` | Xóa mềm |


Cấu trúc d:/EMS_frontend/ — 51 files
Để chạy, bạn cần:

cd d:/EMS_frontend
npm install
cp .env.example .env   # sửa VITE_API_BASE_URL nếu backend chạy port khác
npm run dev            # → http://localhost:3000
Những gì đã có (kết nối API thật):
Module	Tính năng
Dashboard	Thống kê tổng số HS/GV, danh sách mới nhất, gọi 4 API song song
Học sinh	CRUD đầy đủ, filter search + trạng thái, phân trang, audit status transition
Giáo viên	CRUD đầy đủ, filter search + trạng thái, phân trang, audit status transition
Lớp học / Điểm / Lương	Placeholder — sẵn sàng kết nối khi API xây dựng xong
Architecture highlights:
src/api/ — Axios client với interceptors (401 auto redirect, toast lỗi)
src/features/{module}/hooks/ — TanStack Query: auto cache, invalidate, loading states
src/features/{module}/schemas/ — Zod validation cho tất cả forms
src/stores/auth.store.ts — Zustand với persist (sẵn sàng khi auth API xong)
Status transitions — enforce đúng theo logic backend (VD: graduated → không thể chuyển)
Khi bạn xây xong API tiếp theo (classrooms, grading, salary...), hãy báo tôi và tôi sẽ kết nối UI ngay!