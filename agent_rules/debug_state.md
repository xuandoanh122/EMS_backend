# Quy trình Debug EMS Backend

## 1. Thứ tự Debug (Priority Order)

### Nguyên tắc chung:
- **Lỗi unexpected (lỗi không mong đợi)**: Check code trước, tìm đến file, sửa lỗi trong code trước
- **Sau khi sửa xong**: Nếu cần thì chạy terminal để verify, không phải lúc nào cũng check trong terminal
- **Cuối cùng**: Tự viết unit test để verify

### Quy trình cụ thể cho Authentication/Login/Database:

#### Bước 1: Tìm lỗi trong code (KHÔNG chạy terminal)
- Đọc code trong các file liên quan
- Tìm hiểu flow hoạt động
- Xác định nguyên nhân lỗi

#### Bước 2: Sửa lỗi trong code
- Fix bug trực tiếp trong file code
- Đảm bảo logic đúng

#### Bước 3: Chạy terminal để verify (nếu cần)
- Chạy server và test API
- Kiểm tra logs

#### Bước 4: Viết unit test (bắt buộc)
- Tự viết unit test cho chức năng đã fix
- Đảm bảo test cover các case

---
Sau đó clean các terminal scripts đã chạy thành công

## 2. Các Terminal Scripts đã chạy thành công

### Kiểm tra MSSQL trực tiếp:
```python
import pyodbc
conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=ems_db;UID=ems_server;PWD=Maiyeuem123@'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users')
print(cursor.fetchone()[0])
```

### Kiểm tra SQLite backup:
```python
import sqlite3
conn = sqlite3.connect('ems_backup.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print(cursor.fetchall())
```

### Chạy server:
```bash
cd d:/EMS_backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Cách Check Database

### 3.1. Kiểm tra xem server đang dùng MSSQL hay SQLite:
- **Qua logs**: Khi server khởi động, xem dòng "Connected to..."
- **Qua API**: Gọi endpoint và xem response
- **Qua code**: Chạy script check_app_db.py

### 3.2. Kiểm tra dữ liệu trong MSSQL:
- Dùng pyodbc kết nối trực tiếp
- Chạy SQL queries để xem tables, rows

### 3.3. Kiểm tra database connection:
```python
# Test MSSQL connection
import pyodbc
try:
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=ems_db;UID=ems_server;PWD=Maiyeuem123@', timeout=5)
    print("MSSQL: OK")
    conn.close()
except Exception as e:
    print(f"MSSQL: FAILED - {e}")
```

---

## 4. Cách Run Server

### 4.1. Chạy server chính:
```bash
cd d:/EMS_backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2. Chạy server local:
```bash
cd d:/EMS_backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4.3. Kiểm tra server đang chạy:
```bash
curl http://127.0.0.1:8000/api/v1/health
```

---

## 5. Quy trình tối ưu khi Debug

### 5.1. Khi gặp lỗi Authentication/Login:

1. **Đọc code trong auth module** - Xem flow xử lý
2. **Tìm lỗi trong service/repository** - Xác định nguyên nhân
3. **Sửa lỗi trong code** - Fix trực tiếp
4. **Verify bằng curl** - Test API
5. **Viết unit test** - Đảm bảo cover case đã fix

### 5.2. Khi gặp lỗi Database Connection:

1. **Kiểm tra code database.py** - Xem logic kết nối
2. **Kiểm tra SQL Server đang chạy**: Services > SQL Server (MSSQLSERVER)
3. **Kiểm tra credentials trong .env**
4. **Kiểm tra port 1433 không bị block**

### 5.3. Checklist Debug Authentication:
- [ ] Server đang dùng MSSQL (không phải SQLite)
- [ ] Teachers table có dữ liệu
- [ ] Users table có dữ liệu
- [ ] User có is_active = True
- [ ] User có teacher_id khớp với teachers table
- [ ] Password đúng

---

## 6. Các lỗi thường gặp và cách fix

| Lỗi | Nguyên nhân | Cách fix |
|------|-------------|----------|
| Server dùng SQLite | MSSQL không kết nối | Kiểm tra MSSQL đang chạy, kiểm tra .env |
| Login lỗi 401 | User không tồn tại hoặc sai password | Tạo user hoặc reset password |
| Teachers = 0 | Chưa import dữ liệu | Import teachers vào MSSQL |
| Users = 0 | Chưa tạo account | Tạo qua API /auth/teachers/{id}/account |
| MSSQL Connection Error | SQL Server không chạy | Start SQL Server service |
| API 404 Not Found | Endpoint chưa được tạo | Thêm endpoint trong controller |

---

## 7. Lưu ý quan trọng

1. **MSSQL là database chính** - SQLite chỉ là fallback
2. **Luôn kiểm tra code trước** - Không phải lúc nào cũng cần chạy terminal
3. **Dùng pyodbc để query trực tiếp** - Để xác định vấn đề nằm ở đâu
4. **Kiểm tra credentials** - .env phải có thông tin đúng
5. **Khởi động lại server** - Sau khi thay đổi .env
6. **Viết unit test sau khi fix** - Đảm bảo code hoạt động đúng
