"""
Unit tests for password reset and user management features.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.modules.auth.service import AuthService
from app.modules.auth.entity import User, UserRole, PasswordResetToken
from app.core.exceptions.common import NotFoundException, ValidationException


class MockSession:
    """Mock database session."""
    
    def __init__(self):
        self.commited = False
        self.rolled_back = False
    
    async def commit(self):
        self.commited = True
    
    async def rollback(self):
        self.rolled_back = True
    
    async def refresh(self, obj):
        pass
    
    def add(self, obj):
        pass
    
    def delete(self, obj):
        pass
    
    def execute(self, *args, **kwargs):
        return MagicMock()


class MockTeacher:
    """Mock teacher entity."""
    
    def __init__(self):
        self.id = 1
        self.full_name = "Test Teacher"
        self.email = "teacher@test.com"
        self.teacher_code = "TCHR001"


class TestPasswordReset:
    """Test cases for password reset functionality."""
    
    @pytest.fixture
    def mock_session(self):
        return MockSession()
    
    @pytest.fixture
    def mock_repo(self, mock_session):
        repo = AsyncMock()
        repo.get_user_by_email = AsyncMock(return_value=None)
        repo.create_password_reset_token = AsyncMock()
        repo.get_valid_password_reset_token = AsyncMock(return_value=None)
        repo.mark_password_reset_token_used = AsyncMock()
        repo.get_user_by_id = AsyncMock(return_value=None)
        repo.update_user = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_forgot_password_non_existent_email(self, mock_session, mock_repo):
        """Test forgot password with non-existent email returns success to avoid enumeration."""
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            result = await service.forgot_password("nonexistent@test.com")
            
            assert "message" in result
            assert "Nếu email tồn tại" in result["message"]
    
    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, mock_session, mock_repo):
        """Test forgot password with existing user sends email."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.username = "testuser"
        mock_user.teacher = MockTeacher()
        
        mock_repo.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_repo.create_password_reset_token = AsyncMock()
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            with patch('app.utils.emailer.send_password_reset_email', return_value=True):
                service = AuthService(mock_session)
                service._repo = mock_repo
                
                result = await service.forgot_password("teacher@test.com")
                
                assert "message" in result
                mock_repo.create_password_reset_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, mock_session, mock_repo):
        """Test reset password with invalid token raises error."""
        mock_repo.get_valid_password_reset_token = AsyncMock(return_value=None)
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            with pytest.raises(ValidationException) as exc_info:
                await service.reset_password("invalid_token", "newpass123")
            
            assert "Token không hợp lệ" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_reset_password_short_password(self, mock_session, mock_repo):
        """Test reset password with too short password raises error."""
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            with pytest.raises(ValidationException) as exc_info:
                await service.reset_password("valid_token", "123")
            
            assert "ít nhất 6 ký tự" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, mock_session, mock_repo):
        """Test change password with wrong old password raises error."""
        from app.core.security import verify_password
        
        mock_user = MagicMock()
        mock_user.password_hash = "hashed_password"
        
        mock_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            with patch('app.core.security.verify_password', return_value=False):
                service = AuthService(mock_session)
                service._repo = mock_repo
                
                with pytest.raises(HTTPException) as exc_info:
                    await service.change_password(1, "wrong_old", "newpass123")
                
                assert exc_info.value.status_code == 401


class TestUserManagement:
    """Test cases for user management functionality."""
    
    @pytest.fixture
    def mock_session(self):
        return MockSession()
    
    @pytest.fixture
    def mock_repo(self, mock_session):
        repo = AsyncMock()
        repo.get_user_by_id = AsyncMock(return_value=None)
        repo.update_user = AsyncMock()
        repo.delete_user = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, mock_session, mock_repo):
        """Test deactivating non-existent user raises error."""
        mock_repo.get_user_by_id = AsyncMock(return_value=None)
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            with pytest.raises(NotFoundException):
                await service.deactivate_user(999)
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, mock_session, mock_repo):
        """Test deactivating user successfully."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.is_active = True
        
        mock_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_repo.update_user = AsyncMock()
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            result = await service.deactivate_user(1)
            
            assert result["is_active"] is False
            assert mock_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_reactivate_user_success(self, mock_session, mock_repo):
        """Test reactivating user successfully."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.is_active = False
        
        mock_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_repo.update_user = AsyncMock()
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            result = await service.reactivate_user(1)
            
            assert result["is_active"] is True
            assert mock_user.is_active is True
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_session, mock_repo):
        """Test deleting user successfully."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        mock_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_repo.delete_user = AsyncMock()
        
        with patch('app.modules.auth.service.AuthRepository', return_value=mock_repo):
            service = AuthService(mock_session)
            service._repo = mock_repo
            
            result = await service.delete_user(1)
            
            assert "thành công" in result["message"]
            mock_repo.delete_user.assert_called_once_with(mock_user)


class TestEmailTemplates:
    """Test email templates are correctly configured."""
    
    def test_send_password_reset_email_import(self):
        """Test password reset email function can be imported."""
        from app.utils.emailer import send_password_reset_email
        assert send_password_reset_email is not None
    
    def test_send_teacher_account_email_import(self):
        """Test teacher account email function can be imported."""
        from app.utils.emailer import send_teacher_account_email
        assert send_teacher_account_email is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
