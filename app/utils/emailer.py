"""
Email Alert Manager - Dùng để gửi email thông báo.

Cấu hình qua biến môi trường:
    EMAIL_SENDER    : địa chỉ Gmail gửi đi  (vd: monitor@gmail.com)
    EMAIL_PASSWORD  : App Password của Gmail  (16 ký tự, không phải mật khẩu đăng nhập)
    EMAIL_RECEIVER  : địa chỉ nhận cảnh báo  (vd: admin@company.com, có thể nhiều địa chỉ cách nhau dấu phẩy)

Cách tạo App Password Gmail:
    1. Bật 2-Step Verification tại myaccount.google.com
    2. Vào myaccount.google.com/apppasswords
    3. Tạo App Password cho "Mail" → copy 16 ký tự → set EMAIL_PASSWORD

Cách dùng:
    from app.utils.emailer import send_email

    # Gửi email
    send_email(
        to="teacher@school.edu.vn",
        subject="Tài khoản Giáo viên",
        html_body="<h1>Xin chào!</h1>..."
    )
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("emailer")

# ========= CẤU HÌNH QUA ENV VAR =========
_SENDER = os.getenv("EMAIL_SENDER", os.getenv("ALERT_EMAIL_SENDER", ""))
_PASSWORD = os.getenv("EMAIL_PASSWORD", os.getenv("ALERT_EMAIL_PASSWORD", ""))
_RECEIVER = os.getenv("EMAIL_RECEIVER", os.getenv("ALERT_EMAIL_RECEIVER", ""))


def is_configured() -> bool:
    """Kiểm tra đã cấu hình email chưa."""
    return bool(_SENDER and _PASSWORD)


def send_email(
    to: str | list[str],
    subject: str,
    html_body: str,
    plain_body: str | None = None,
) -> bool:
    """
    Gửi email đến một hoặc nhiều địa chỉ.
    
    Args:
        to: Địa chỉ email nhận (string hoặc list)
        subject: Tiêu đề email
        html_body: Nội dung email dạng HTML
        plain_body: Nội dung email dạng text thuần (optional)
    
    Returns:
        True nếu gửi thành công, False nếu thất bại
    """
    if not is_configured():
        logger.warning(
            "Email chưa cấu hình (EMAIL_SENDER/PASSWORD/RECEIVER). "
            "Subject: %s", subject
        )
        return False

    # Convert to list
    if isinstance(to, str):
        receivers = [r.strip() for r in to.split(",") if r.strip()]
    else:
        receivers = [r.strip() for r in to if r.strip()]
    
    if not receivers:
        logger.warning("Không có người nhận hợp lệ")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = _SENDER
        msg["To"] = ", ".join(receivers)
        
        # Attach plain text version
        if plain_body:
            msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        
        # Attach HTML version
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(_SENDER, _PASSWORD)
            smtp.sendmail(_SENDER, receivers, msg.as_string())

        logger.info("Email sent — subject: %s → %s", subject, receivers)
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail authentication failed! "
            "Kiểm tra EMAIL_SENDER và EMAIL_PASSWORD (phải là App Password)."
        )
    except Exception as e:
        logger.error("Gửi email thất bại: %s", e)
    
    return False


def send_teacher_account_email(
    teacher_email: str,
    teacher_name: str,
    teacher_code: str,
    temp_password: str,
    login_url: str = "http://localhost:3000/login",
) -> bool:
    """
    Gửi email thông báo tài khoản Giáo viên.
    
    Args:
        teacher_email: Email của giáo viên
        teacher_name: Tên giáo viên
        teacher_code: Mã giáo viên
        temp_password: Mật khẩu tạm thời
        login_url: URL đăng nhập
    
    Returns:
        True nếu gửi thành công
    """
    subject = f"[EMS] Tài khoản Giáo viên - {teacher_name}"
    
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;">
      <div style="background:#4F46E5;color:white;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">🎓 Tài khoản Giáo viên</h2>
      </div>
      <div style="padding:20px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;">
        <p>Xin chào <strong>{teacher_name}</strong>,</p>
        
        <p>Hệ thống Quản lý Giáo dục (EMS) đã tạo tài khoản cho bạn:</p>
        
        <table style="width:100%;margin:20px 0;border-collapse:collapse;">
          <tr>
            <td style="padding:8px 12px;background:#f9fafb;border:1px solid #e5e7eb;font-weight:bold;width:140px;">Mã Giáo viên</td>
            <td style="padding:8px 12px;border:1px solid #e5e7eb;">{teacher_code}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;background:#f9fafb;border:1px solid #e5e7eb;font-weight:bold;">Email</td>
            <td style="padding:8px 12px;border:1px solid #e5e7eb;">{teacher_email}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;background:#f9fafb;border:1px solid #e5e7eb;font-weight:bold;">Mật khẩu</td>
            <td style="padding:8px 12px;border:1px solid #e5e7eb;font-family:monospace;font-size:16px;color:#dc2626;">{temp_password}</td>
          </tr>
        </table>
        
        <div style="background:#FEF3C7;padding:12px;border-radius:6px;margin:20px 0;">
          <strong>⚠️ Lưu ý quan trọng:</strong>
          <ul style="margin:8px 0 0 0;">
            <li>Đây là mật khẩu tạm thời. Bạn <strong>phải đổi mật khẩu</strong> sau khi đăng nhập lần đầu.</li>
            <li>Vui lòng đổi mật khẩu ngay để bảo mật tài khoản.</li>
          </ul>
        </div>
        
        <p>Click vào nút bên dưới để đăng nhập:</p>
        <p style="text-align:center;margin:20px 0;">
          <a href="{login_url}" style="display:inline-block;background:#4F46E5;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;">
            Đăng nhập ngay
          </a>
        </p>
        
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
        <p style="color:#6B7280;font-size:12px;">
          Nếu bạn gặp vấn đề, vui lòng liên hệ quản trị viên hệ thống.
        </p>
        <p style="color:#9CA3AF;font-size:11px;margin-top:20px;">
          Email được gửi tự động từ Hệ thống Quản lý Giáo dục - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
      </div>
    </body></html>
    """
    
    plain_body = f"""
Xin chào {teacher_name},

Hệ thống Quản lý Giáo dục (EMS) đã tạo tài khoản cho bạn:

Mã Giáo viên: {teacher_code}
Email: {teacher_email}
Mật khẩu: {temp_password}

⚠️ Lưu ý: Đây là mật khẩu tạm thời. Bạn PHẢI đổi mật khẩu sau khi đăng nhập lần đầu.

Đăng nhập tại: {login_url}

---
Email được gửi tự động từ Hệ thống Quản lý Giáo dục
    """
    
    return send_email(
        to=teacher_email,
        subject=subject,
        html_body=html_body,
        plain_body=plain_body,
    )


def send_password_reset_email(
    email: str,
    user_name: str,
    reset_token: str,
    reset_url: str = "http://localhost:3000/reset-password",
) -> bool:
    """
    Gửi email chứa link reset mật khẩu.
    
    Args:
        email: Email người nhận
        user_name: Tên người dùng
        reset_token: Token reset
        reset_url: URL reset password
    
    Returns:
        True nếu gửi thành công
    """
    full_reset_url = f"{reset_url}?token={reset_token}"
    
    subject = f"[EMS] Đặt lại mật khẩu - {user_name}"
    
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;">
      <div style="background:#DC2626;color:white;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">🔐 Đặt lại mật khẩu</h2>
      </div>
      <div style="padding:20px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;">
        <p>Xin chào <strong>{user_name}</strong>,</p>
        
        <p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.</p>
        
        <p>Click vào nút bên dưới để đặt lại mật khẩu:</p>
        <p style="text-align:center;margin:20px 0;">
          <a href="{full_reset_url}" style="display:inline-block;background:#DC2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;">
            Đặt lại mật khẩu
          </a>
        </p>
        
        <p style="font-size:12px;color:#6B7280;">
          Link này sẽ hết hạn sau <strong>30 phút</strong>.
        </p>
        
        <div style="background:#FEF3C7;padding:12px;border-radius:6px;margin:20px 0;">
          <strong>⚠️ Lưu ý an toàn:</strong>
          <ul style="margin:8px 0 0 0;">
            <li>Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.</li>
            <li>Không chia sẻ link này với bất kỳ ai.</li>
          </ul>
        </div>
        
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
        <p style="color:#9CA3AF;font-size:11px;margin-top:20px;">
          Email được gửi tự động từ Hệ thống Quản lý Giáo dục - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
      </div>
    </body></html>
    """
    
    plain_body = f"""
Xin chào {user_name},

Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.

Link đặt lại mật khẩu: {full_reset_url}

Link này sẽ hết hạn sau 30 phút.

Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.

---
Email được gửi tự động từ Hệ thống Quản lý Giáo dục
    """
    
    return send_email(
        to=email,
        subject=subject,
        html_body=html_body,
        plain_body=plain_body,
    )
