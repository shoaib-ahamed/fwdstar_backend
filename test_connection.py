#!/usr/bin/env python3
"""
Quick test script to verify Supabase connection and run basic tests.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog


async def test_database_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Database connected!")
            print(f"   Version: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed!")
        print(f"   Error: {e}")
        return False


async def test_table_creation():
    """Test if required tables exist."""
    print("\n📋 Checking tables...")
    try:
        async with AsyncSessionLocal() as session:
            # Check users table
            result = await session.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')")
            )
            users_exists = result.scalar()
            print(f"   {'✅' if users_exists else '❌'} users table exists")

            # Check audit_logs table
            result = await session.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs')")
            )
            audit_exists = result.scalar()
            print(f"   {'✅' if audit_exists else '❌'} audit_logs table exists")

            return users_exists and audit_exists
    except Exception as e:
        print(f"❌ Table check failed!")
        print(f"   Error: {e}")
        return False


async def test_user_creation():
    """Test creating a user."""
    print("\n👤 Testing user creation...")
    try:
        async with AsyncSessionLocal() as session:
            # Check if we can create a user
            test_user = User(
                email="test.connection@example.com",
                password_hash="$2b$12$test_hash",
                role=UserRole.SHIPPER
            )
            session.add(test_user)
            await session.commit()
            print(f"   ✅ User creation test passed")
            return True
    except Exception as e:
        print(f"   ❌ User creation test failed!")
        print(f"   Error: {e}")
        return False


async def run_all_tests():
    """Run all connection tests."""
    print("=" * 60)
    print("🚀 FwdStar Auth API - Database Connection Test")
    print("=" * 60)

    results = {
        "Database Connection": await test_database_connection(),
        "Table Creation": await test_table_creation(),
        "User Creation": await test_user_creation()
    }

    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All tests passed! Your Supabase setup is working correctly!")
        print("\n📖 Next steps:")
        print("   1. Start the server: uvicorn app.main:app --reload")
        print("   2. Open Swagger UI: http://localhost:8000/docs")
        print("   3. Test the endpoints!")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("   1. Your .env file has correct DATABASE_URL")
        print("   2. Supabase project is active")
        print("   3. Run migrations: alembic upgrade head")

    return all_passed


if __name__ == "__main__":
    asyncio.run(run_all_tests())
