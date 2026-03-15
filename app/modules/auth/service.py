"""
Auth service.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.core.exceptions.auth import (
    AccountDisabledException,
    InvalidCredentialsException,
    TokenBlacklistedException,
    TokenInvalidException,
)
from app.core.exceptions.common import AlreadyExistsException, NotFoundException, ValidationException
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.dto import (
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.auth.entity import User, UserRole
from app.modules.auth.repository import AuthRepository


class AuthService:
    def __init__(self, session) -> None:
        self._repo = AuthRepository(session)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self._repo.get_user_by_username(username)
        if not user:
            raise InvalidCredentialsException()
        if not user.is_active:
            raise AccountDisabledException()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        token_data = {"sub": str(user.id), "role": user.role.value, "teacher_id": user.teacher_id}
        access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data=token_data, expires_delta=refresh_token_expires)

        await self._repo.update_last_login(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            role=user.role,
            user_id=user.id,
            teacher_id=user.teacher_id,
        )

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        payload = decode_token(data.refresh_token)
        token_type = payload.get("type")
        jti = payload.get("jti")
        if token_type != "refresh" or not jti:
            raise TokenInvalidException()

        if await self._repo.is_blacklisted(jti):
            raise TokenBlacklistedException()

        user_id_raw = payload.get("sub")
        role = payload.get("role")
        teacher_id = payload.get("teacher_id")
        if not user_id_raw or not role:
            raise TokenInvalidException()

        user = await self._repo.get_user_by_id(int(user_id_raw))
        if not user or not user.is_active:
            raise AccountDisabledException()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        token_data = {"sub": str(user.id), "role": user.role.value, "teacher_id": user.teacher_id}
        access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data=token_data, expires_delta=refresh_token_expires)

        # Rotate refresh token: blacklist old one
        exp_ts = payload.get("exp")
        if exp_ts:
            await self._repo.add_blacklist(
                jti=jti,
                token_type="refresh",
                expires_at=datetime.utcfromtimestamp(exp_ts),
            )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            role=user.role,
            user_id=user.id,
            teacher_id=user.teacher_id,
        )

    async def logout(self, data: LogoutRequest) -> None:
        payload = decode_token(data.token)
        token_type = payload.get("type")
        jti = payload.get("jti")
        if not jti:
            raise TokenInvalidException()

        exp_ts = payload.get("exp")
        if exp_ts is None:
            raise TokenInvalidException()

        if token_type not in ("access", "refresh"):
            raise TokenInvalidException()

        if data.token_type and data.token_type != token_type:
            raise TokenInvalidException()

        await self._repo.add_blacklist(
            jti=jti,
            token_type=token_type,
            expires_at=datetime.utcfromtimestamp(exp_ts),
        )

    async def create_user(self, data: UserCreateRequest) -> UserResponse:
        existing = await self._repo.get_user_by_username(data.username)
        if existing:
            raise AlreadyExistsException(resource="User", identifier=data.username)

        if data.role == UserRole.TEACHER:
            if not data.teacher_id:
                raise ValidationException(detail="teacher_id is required for teacher role")
            teacher = await self._repo.get_teacher_by_id(data.teacher_id)
            if not teacher:
                raise NotFoundException(resource="Teacher", identifier=str(data.teacher_id))

        user = User(
            username=data.username,
            password_hash=get_password_hash(data.password),
            role=data.role,
            teacher_id=data.teacher_id,
            is_active=True,
        )
        created = await self._repo.create_user(user)
        return UserResponse.model_validate(created)

    async def list_users(
        self,
        page: int,
        page_size: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> UserListResponse:
        users, total = await self._repo.list_users(page, page_size, role, is_active)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdateRequest) -> UserResponse:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))

        update_data = data.model_dump(exclude_none=True)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        if "role" in update_data and update_data["role"] == UserRole.TEACHER:
            teacher_id = update_data.get("teacher_id") or user.teacher_id
            if not teacher_id:
                raise ValidationException(detail="teacher_id is required for teacher role")
            teacher = await self._repo.get_teacher_by_id(teacher_id)
            if not teacher:
                raise NotFoundException(resource="Teacher", identifier=str(teacher_id))

        updated = await self._repo.update_user(user, update_data)
        return UserResponse.model_validate(updated)

    async def create_teacher_account(self, teacher_id: int, send_email: bool = True) -> dict:
        """
        Tạo tài khoản cho Giáo viên.
        
        Args:
            teacher_id: ID của giáo viên
            send_email: Có gửi email thông báo không
        
        Returns:
            Dict chứa thông tin tài khoản đã tạo
        """
        import secrets
        import string
        
        # Lấy thông tin giáo viên
        teacher = await self._repo.get_teacher_by_id(teacher_id)
        if not teacher:
            raise NotFoundException(resource="Teacher", identifier=str(teacher_id))
        
        if not teacher.email:
            raise ValidationException(detail="Gi\u00e1o vi\u00ean ch\u01b0a c\u00f3 email, kh\u00f4ng th\u1ec3 t\u1ea1o t\u00e0i kho\u1ea3n")
        
        # Kiểm tra đã có tài khoản chưa
        if teacher.id and await self._repo.get_user_by_teacher_id(teacher_id):
            raise AlreadyExistsException(resource="User", identifier=f"teacher_id={teacher_id}")
        
        # Tạo username từ email
        username = teacher.email.split("@")[0].lower()
        # Đảm bảo username unique
        base_username = username
        counter = 1
        while await self._repo.get_user_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1
        
        # Tạo mật khẩu tạm thời
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        
        # Tạo user
        user = User(
            username=username,
            password_hash=get_password_hash(temp_password),
            role=UserRole.TEACHER,
            teacher_id=teacher_id,
            is_active=True,
            must_change_password=True,
        )
        created = await self._repo.create_user(user)
        
        # Gửi email
        email_sent = False
        if send_email and teacher.email:
            try:
                from app.utils.emailer import send_teacher_account_email
                email_sent = send_teacher_account_email(
                    teacher_email=teacher.email,
                    teacher_name=teacher.full_name,
                    teacher_code=teacher.teacher_code,
                    temp_password=temp_password,
                )
            except Exception as e:
                # Log error but don't fail the operation
                import logging
                logging.getLogger("auth").error(f"Failed to send email: {e}")
        
        return {
            "user_id": created.id,
            "teacher_id": teacher.id,
            "teacher_code": teacher.teacher_code,
            "teacher_name": teacher.full_name,
            "email": teacher.email,
            "username": created.username,
            "temp_password": temp_password,
            "email_sent": email_sent,
            "must_change_password": created.must_change_password,
        }

    # ----------------------------------------------------------------
    # Password Reset
    # ----------------------------------------------------------------

    async def forgot_password(self, email: str) -> dict:
        """
        Xử lý yêu cầu quên mật khẩu.
        
        Args:
            email: Email của tài khoản
        
        Returns:
            Thông báo đã gửi email reset (luôn trả về thành công để tránh email enumeration)
        """
        import logging
        logger = logging.getLogger("auth")
        
        # Luôn trả về thành công để tránh email enumeration attack
        try:
            # Tìm user qua email
            user = await self._repo.get_user_by_email(email)
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email}")
                return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}
            
            # Kiểm tra user có active không
            if not user.is_active:
                logger.warning(f"Password reset requested for disabled user: {email}")
                return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}
            
            # Tạo token reset
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(minutes=30)
            
            from app.modules.auth.entity import PasswordResetToken
            token_obj = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at,
            )
            
            await self._repo.create_password_reset_token(token_obj)
            
            # Gửi email
            user_name = user.teacher.full_name if user.teacher else user.username
            
            try:
                from app.utils.emailer import send_password_reset_email
                send_password_reset_email(
                    email=email,
                    user_name=user_name,
                    reset_token=reset_token,
                )
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")
            
            return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}
        
        except Exception as e:
            logger.error(f"Error in forgot_password: {e}")
            return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}

    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Đặt lại mật khẩu với token.
        
        Args:
            token: Token reset mật khẩu
            new_password: Mật khẩu mới
        
        Returns:
            Thông báo thành công
        """
        # Validate password
        if len(new_password) < 6:
            raise ValidationException(detail="Mật khẩu phải có ít nhất 6 ký tự")
        
        # Lấy token
        token_obj = await self._repo.get_valid_password_reset_token(token)
        if not token_obj:
            raise ValidationException(detail="Token không hợp lệ hoặc đã hết hạn")
        
        # Lấy user
        user = await self._repo.get_user_by_id(token_obj.user_id)
        if not user or not user.is_active:
            raise ValidationException(detail="Tài khoản không hợp lệ")
        
        # Đổi mật khẩu
        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        await self._repo.update_user(user, {})
        
        # Đánh dấu token đã sử dụng
        await self._repo.mark_password_reset_token_used(token_obj)
        
        return {"message": "Đặt lại mật khẩu thành công"}

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> dict:
        """
        Đổi mật khẩu khi đã đăng nhập.
        
        Args:
            user_id: ID của user
            old_password: Mật khẩu cũ
            new_password: Mật khẩu mới
        
        Returns:
            Thông báo thành công
        """
        # Validate password
        if len(new_password) < 6:
            raise ValidationException(detail="Mật khẩu phải có ít nhất 6 ký tự")
        
        # Lấy user
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise InvalidCredentialsException()
        
        # Đổi mật khẩu
        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        await self._repo.update_user(user, {})
        
        return {"message": "Đổi mật khẩu thành công"}

    async def deactivate_user(self, user_id: int) -> dict:
        """
        Vô hiệu hóa tài khoản (soft delete).
        
        Args:
            user_id: ID của user cần vô hiệu hóa
        
        Returns:
            Thông tin user đã bị vô hiệu hóa
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        user.is_active = False
        await self._repo.update_user(user, {})
        
        return {
            "message": "Vô hiệu hóa tài khoản thành công",
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active,
        }

    async def reactivate_user(self, user_id: int) -> dict:
        """
        Kích hoạt lại tài khoản.
        
        Args:
            user_id: ID của user cần kích hoạt
        
        Returns:
            Thông tin user đã được kích hoạt
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        user.is_active = True
        await self._repo.update_user(user, {})
        
        return {
            "message": "Kích hoạt tài khoản thành công",
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active,
        }

    async def delete_user(self, user_id: int) -> dict:
        """
        Xóa vĩnh viễn tài khoản (hard delete).
        
        Args:
            user_id: ID của user cần xóa
        
        Returns:
            Thông báo thành công
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        username = user.username
        await self._repo.delete_user(user)
        
        return {
            "message": f"Xóa tài khoản '{username}' thành công",
            "user_id": user_id,
        }

    # ----------------------------------------------------------------
    # Password Reset
    # ----------------------------------------------------------------

    async def forgot_password(self, email: str) -> dict:
        """
        Xử lý yêu cầu quên mật khẩu.
        
        Args:
            email: Email của tài khoản
        
        Returns:
            Thông báo đã gửi email reset (luôn trả về thành công để tránh email enumeration)
        """
        import logging
        logger = logging.getLogger("auth")
        
        # Luôn trả về thành công để tránh email enumeration attack
        try:
            # Tìm user qua email
            user = await self._repo.get_user_by_email(email)
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email}")
                return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}
            
            # Kiểm tra user có active không
            if not user.is_active:
                logger.warning(f"Password reset requested for disabled user: {email}")
                return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}
            
            # Tạo token reset
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(minutes=30)
            
            from app.modules.auth.entity import PasswordResetToken
            token_obj = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at,
            )
            
            await self._repo.create_password_reset_token(token_obj)
            
            # Gửi email
            user_name = user.teacher.full_name if user.teacher else user.username
            
            try:
                from app.utils.emailer import send_password_reset_email
                send_password_reset_email(
                    email=email,
                    user_name=user_name,
                    reset_token=reset_token,
                )
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")
            
            return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}
        
        except Exception as e:
            logger.error(f"Error in forgot_password: {e}")
            return {"message": "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu."}

    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Đặt lại mật khẩu với token.
        
        Args:
            token: Token reset mật khẩu
            new_password: Mật khẩu mới
        
        Returns:
            Thông báo thành công
        """
        # Validate password
        if len(new_password) < 6:
            raise ValidationException(detail="Mật khẩu phải có ít nhất 6 ký tự")
        
        # Lấy token
        token_obj = await self._repo.get_valid_password_reset_token(token)
        if not token_obj:
            raise ValidationException(detail="Token không hợp lệ hoặc đã hết hạn")
        
        # Lấy user
        user = await self._repo.get_user_by_id(token_obj.user_id)
        if not user or not user.is_active:
            raise ValidationException(detail="Tài khoản không hợp lệ")
        
        # Đổi mật khẩu
        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        await self._repo.update_user(user, {})
        
        # Đánh dấu token đã sử dụng
        await self._repo.mark_password_reset_token_used(token_obj)
        
        return {"message": "Đặt lại mật khẩu thành công"}

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> dict:
        """
        Đổi mật khẩu khi đã đăng nhập.
        
        Args:
            user_id: ID của user
            old_password: Mật khẩu cũ
            new_password: Mật khẩu mới
        
        Returns:
            Thông báo thành công
        """
        # Validate password
        if len(new_password) < 6:
            raise ValidationException(detail="Mật khẩu phải có ít nhất 6 ký tự")
        
        # Lấy user
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise InvalidCredentialsException()
        
        # Đổi mật khẩu
        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        await self._repo.update_user(user, {})
        
        return {"message": "Đổi mật khẩu thành công"}

    async def deactivate_user(self, user_id: int) -> dict:
        """
        Vô hiệu hóa tài khoản (soft delete).
        
        Args:
            user_id: ID của user cần vô hiệu hóa
        
        Returns:
            Thông tin user đã bị vô hiệu hóa
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        # Không cho phép tự vô hiệu hóa
        # (sẽ kiểm tra ở controller level)
        
        user.is_active = False
        await self._repo.update_user(user, {})
        
        return {
            "message": "Vô hiệu hóa tài khoản thành công",
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active,
        }

    async def reactivate_user(self, user_id: int) -> dict:
        """
        Kích hoạt lại tài khoản.
        
        Args:
            user_id: ID của user cần kích hoạt
        
        Returns:
            Thông tin user đã được kích hoạt
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        user.is_active = True
        await self._repo.update_user(user, {})
        
        return {
            "message": "Kích hoạt tài khoản thành công",
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active,
        }

    async def delete_user(self, user_id: int) -> dict:
        """
        Xóa vĩnh viễn tài khoản (hard delete).
        
        Args:
            user_id: ID của user cần xóa
        
        Returns:
            Thông báo thành công
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        
        # Không cho phép tự xóa
        # (sẽ kiểm tra ở controller level)
        
        username = user.username
        await self._repo.delete_user(user)
        
        return {
            "message": f"Xóa tài khoản '{username}' thành công",
            "user_id": user_id,
        }
