#!/usr/bin/env python
"""
CLI script to bootstrap the first admin user.

Usage:
    python -m app.scripts.create_admin --username admin --password your_password
"""

import argparse
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(
        description="Create the first admin user for EMS"
    )
    parser.add_argument(
        "--username", 
        required=True,
        help="Admin username (min 3 chars)"
    )
    parser.add_argument(
        "--password", 
        required=True,
        help="Admin password (min 6 chars)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if len(args.username) < 3:
        print("[X] Username must be at least 3 characters")
        sys.exit(1)
    
    if len(args.password) < 6:
        print("[X] Password must be at least 6 characters")
        sys.exit(1)
    
    print("Creating admin user...")
    print()
    
    async def run():
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize database via app (to use correct connection)
        from app.main import app as _app  # noqa: F401 - this initializes the DB
        from app.core.database import init_db, get_async_session
        from app.modules.auth.entity import User, UserRole
        from sqlalchemy import select
        
        # Use bcrypt directly for password hashing
        import bcrypt
        password_hash = bcrypt.hashpw(args.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Use get_async_session generator
        await init_db()
        async for session in get_async_session():
            try:
                # Check if admin already exists
                result = await session.execute(
                    select(User).where(User.role == UserRole.ADMIN)
                )
                existing_admin = result.scalars().first()
                
                if existing_admin:
                    print(f"[X] Admin user already exists (ID: {existing_admin.id})")
                    print(f"   Username: {existing_admin.username}")
                    sys.exit(1)
                
                # Check if username is taken
                result = await session.execute(
                    select(User).where(User.username == args.username)
                )
                existing_user = result.scalars().first()
                
                if existing_user:
                    print(f"[X] Username '{args.username}' is already taken")
                    sys.exit(1)
                
                # Create admin user
                admin = User(
                    username=args.username,
                    password_hash=password_hash,
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                
                session.add(admin)
                await session.commit()
                await session.refresh(admin)
                
                print(f"[OK] Admin user created successfully!")
                print(f"   ID: {admin.id}")
                print(f"   Username: {admin.username}")
                print(f"   Role: {admin.role.value}")
                print(f"   Status: {'Active' if admin.is_active else 'Inactive'}")
                
                break  # Exit the async generator loop
            finally:
                await session.close()
    
    try:
        asyncio.run(run())
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
