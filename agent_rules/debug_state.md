# Quy trình Debug EMS Backend

## 1. Thứ tự Debug (Priority Order)

Khi gặp vấn đề về authentication/login/database, thực hiện theo thứ tự sau:

### Bước 1: Kiểm tra Server đang chạy
```bash
# Kiểm tra server có đang hoạt động không
curl http://127.0.0.1:8000/api/v1/health
```

### Bước 2: Xem Logs của Server
- Terminal đang chạy uvicorn sẽ hiển thị:
  - `✅ Connected to PRIMARY database (MSSQL @ localhost:1433/ems_db)` = ĐANG DÙNG MSSQL (ĐÚNG)
  - `⚠️  PRIMARY database unavailable` + `✅ Connected to BACKUP database (SQLite)` = ĐANG DÙNG SQLITE (CẦN FIX)

### Bước 3: Kiểm tra Database trực tiếp (MSSQL)
Tạo script debug_db.py:

```python
# debug_db.py
import pyodbc

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=ems_db;UID=ems_server;PWD=Maiyeuem123@'

def check_tables():
    conn = pyodbc.connect(conn_str, timeout=5)
    cursor = conn.cursor()
    
    # Kiểm tra các bảng
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE='BASE TABLE'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tổng số bảng: {len(tables)}")
    
    # Kiểm tra Teachers
    if 'teachers' in tables:
        cursor.execute('SELECT COUNT(*) FROM teachers')
        print(f"Teachers: {cursor.fetchone()[0]}")
    
    # Kiểm tra Users
    if 'users' in tables:
        cursor.execute('SELECT COUNT(*) FROM users')
        print(f"Users: {cursor.fetchone()[0]}")
        
        cursor.execute('SELECT TOP 5 id, username, role, teacher_id, is_active FROM users')
        for row in cursor.fetchall():
            print(f"  User: id={row[0]}, username={row[1]}, role={row[2]}, teacher_id={row[3]}, is_active={row[4]}")
    
    conn.close()

if __name__ == '__main__':
    check_tables()
```

Chạy: `python debug_db.py`

### Bước 4: Kiểm tra App đang dùng Database nào
```python
# check_app_db.py
import asyncio
from app.core.database import init_db, is_using_backup

async def main():
    await init_db()
    print(f"Using backup (SQLite): {is_using_backup()}")

asyncio.run(main())
```

### Bước 5: Test API Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "doanh.nguyen", "password": "V7DOdshwnK"}'
```

---

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

1. **Kiểm tra logs server trước** - Xem database đang dùng
2. **Kiểm tra MSSQL trực tiếp** - Dùng pyodbc query
3. **Kiểm tra users table** - Xem có user chưa, is_active = true không
4. **Test API login** - Gọi trực tiếp curl
5. **Kiểm tra teacher_id** - Đảm bảo user có teacher_id khớp với teachers table

### 5.2. Khi gặp lỗi Database Connection:

1. **Kiểm tra SQL Server đang chạy**: Services > SQL Server (MSSQLSERVER)
2. **Kiểm tra credentials trong .env**
3. **Kiểm tra port 1433 không bị block**
4. **Thử kết nối bằng pyodbc trước**

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

---

## 7. Lưu ý quan trọng

1. **MSSQL là database chính** - SQLite chỉ là fallback
2. **Luôn kiểm tra logs** - Server logs sẽ cho biết đang dùng DB nào
3. **Dùng pyodbc để query trực tiếp** - Để xác định vấn đề nằm ở đâu
4. **Kiểm tra credentials** - .env phải có thông tin đúng
5. **Khởi động lại server** - Sau khi thay đổi .env
