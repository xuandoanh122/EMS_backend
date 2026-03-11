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
  "code": 200,             // HTTP Status Code hoặc Custom Business Code
  "message": "Success",    // Thông báo ngắn gọn
  "detail": "Retrieved student list successfully", // Chi tiết cho developer đọc
  "data": { ... }          // Payload thực tế trả về (chỉ có khi thành công)
}