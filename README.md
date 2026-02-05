# FwdStar Authentication API

A production-grade FastAPI authentication system with maximum security for a B2B freight marketplace. Features JWT tokens stored in httpOnly cookies, role-based access control (RBAC), comprehensive audit logging, and protection against common vulnerabilities (XSS, CSRF, SQL injection, brute force attacks).

## Features

- ✅ **JWT Authentication** - Access and refresh token mechanism
- ✅ **httpOnly Cookies** - XSS protection by storing tokens in httpOnly cookies
- ✅ **Role-Based Access Control** - Four user roles (SHIPPER, CARRIER_OWNER, DRIVER, ADMIN)
- ✅ **Secure Password Hashing** - Bcrypt with cost factor 12
- ✅ **Account Lockout** - Automatic lockout after 5 failed login attempts for 30 minutes
- ✅ **Audit Logging** - All authentication events logged with IP and user agent
- ✅ **CSRF Protection** - SameSite cookies prevent CSRF attacks
- ✅ **SQL Injection Prevention** - SQLAlchemy parameterized queries
- ✅ **Password Validation** - Enforces strong passwords (8+ chars, mixed case, number)
- ✅ **Token Refresh** - Automatic access token renewal
- ✅ **Comprehensive Testing** - 15+ test cases covering all scenarios

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Alembic** - Database migrations
- **PyJWT** - JWT token handling
- **Passlib** - Password hashing
- **Pydantic** - Data validation and serialization
- **Pytest** - Testing framework

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── core/
│   │   ├── config.py              # Pydantic settings
│   │   ├── security.py            # JWT + password functions
│   │   └── database.py            # Async SQLAlchemy setup
│   ├── models/
│   │   ├── user.py                # User model with RBAC
│   │   └── audit_log.py           # Audit log model
│   ├── schemas/
│   │   ├── user.py                # User Pydantic schemas
│   │   └── auth.py                # Auth request/response schemas
│   ├── api/
│   │   ├── deps.py                # Auth dependencies
│   │   └── v1/
│   │       └── auth.py            # Auth endpoints
│   └── services/
│       ├── user_service.py        # User CRUD operations
│       └── audit_service.py       # Audit logging service
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py  # Initial database migration
│   ├── env.py                     # Alembic configuration
│   └── script.py.mako             # Migration template
├── tests/
│   ├── conftest.py                # Test configuration
│   └── test_auth.py               # Comprehensive test suite
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Security Features

### 1. Password Security
- Bcrypt hashing with cost factor 12
- Minimum 8 characters with uppercase, lowercase, and number
- Never log or return passwords

### 2. Token Security
- JWT signed with HS256 algorithm
- Access token expires in 15 minutes
- Refresh token expires in 7 days (30 days if remember_me=True)
- Tokens stored only in httpOnly cookies

### 3. Cookie Security
- `httponly=True` - Prevents JavaScript access (XSS protection)
- `secure=True` - HTTPS only in production
- `samesite=lax` - CSRF protection
- `path=/` or `/api/v1/auth` - Scoped to necessary paths

### 4. Brute Force Protection
- Tracks failed login attempts per user
- Locks account for 30 minutes after 5 failures
- All failures logged with IP address

### 5. SQL Injection Prevention
- SQLAlchemy ORM with parameterized queries
- No string concatenation in database queries
- Async database operations

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd fwdstar_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

**🚀 Option A: Supabase (Cloud PostgreSQL - RECOMMENDED)**

Supabase provides managed PostgreSQL with automatic backups, connection pooling, and real-time features.

**Quick Setup:**
1. Create account at https://supabase.com
2. Create new project
3. Get connection string from Settings > Database
4. Update .env file with Supabase URL

**See detailed guide:** [`SUPABASE_SETUP.md`](SUPABASE_SETUP.md)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with Supabase credentials
# DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres
```

**Option B: Local PostgreSQL (Docker)**

```bash
# Using Docker
docker run --name fwdstar-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fwdstar_dev \
  -p 5432:5432 \
  -d postgres:15

# Or using native PostgreSQL
# Create database: createdb fwdstar_dev
```

**Option C: SQLite (Development Only)**

```bash
# Edit .env file
DATABASE_URL=sqlite+aiosqlite:///./fwdstar.db
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Generate SECRET_KEY
openssl rand -hex 32
# Copy the output to SECRET_KEY in .env

# Edit .env with your settings
nano .env
```

### 4. Database Migration

```bash
# Initialize Alembic (if not done)
alembic init alembic

# Generate initial migration (already done)
# alembic revision --autogenerate -m "Initial schema"

# Run migrations
alembic upgrade head
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --log-level info

# Or
python -m uvicorn app.main:app --reload --log-level info

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

The API will be available at `http://localhost:10000`

## 🚀 Quick Start

### Option 1: Using Setup Script

**Linux/macOS:**
```bash
chmod +x setup_supabase.sh
./setup_supabase.sh
```

**Windows:**
```bash
setup_supabase.bat
```

### Option 2: Manual Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 2. Test database connection
python test_connection.py

# 3. Run migrations
alembic upgrade head

# 4. Start server
uvicorn app.main:app --reload --log-level info
```

## 📚 API Documentation & Swagger UI

### Interactive Documentation

Once the server is running, visit:

- **🔍 Swagger UI** (Interactive): http://localhost:10000/docs
  - Test endpoints directly in browser
  - Automatic request/response documentation
  - Cookie-based authentication

- **📖 ReDoc** (Clean view): http://localhost:10000/redoc
  - Professional API documentation
  - Sidebar navigation
  - Search functionality

- **❤️ Health Check**: http://localhost:10000/health
  - Verify server status

### Swagger UI Features

- ✅ **Interactive Testing** - Try all endpoints in browser
- ✅ **Automatic Documentation** - Request/response schemas
- ✅ **Cookie Handling** - Automatic authentication
- ✅ **Code Generation** - Generate cURL, Python, JavaScript
- ✅ **Error Testing** - Test all error scenarios

### See Full Swagger Guide

For complete Swagger UI documentation, see: [`SWAGGER_GUIDE.md`](SWAGGER_GUIDE.md)

## API Endpoints

### 1. Register User

Register a new user with email, password, and role.

```bash
curl -X POST http://localhost:10000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "shipper@example.com",
    "password": "SecurePass123",
    "role": "SHIPPER"
  }'
```

**Success Response (201):**
```json
{
  "user": {
    "id": "uuid-string",
    "email": "shipper@example.com",
    "role": "SHIPPER",
    "status": "ACTIVE",
    "created_at": "2026-02-04T12:00:00Z"
  },
  "message": "Registration successful"
}
```

**Sets cookies:**
- `access_token` - JWT access token (expires in 15 minutes)
- `refresh_token` - JWT refresh token (expires in 7 days)

### 2. Login

Authenticate user and receive tokens.

```bash
curl -X POST http://localhost:10000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "shipper@example.com",
    "password": "SecurePass123",
    "remember_me": true
  }'
```

**Success Response (200):**
```json
{
  "user": {
    "id": "uuid-string",
    "email": "shipper@example.com",
    "role": "SHIPPER",
    "status": "ACTIVE"
  },
  "message": "Login successful"
}
```

**Error Responses:**
- `401` - Invalid email or password
- `403` - Account locked until {time}

### 3. Get Current User

Get information about the currently authenticated user.

```bash
curl -X GET http://localhost:10000/api/v1/auth/me \
  -H "Cookie: access_token=your_jwt_token"
```

**Success Response (200):**
```json
{
  "id": "uuid-string",
  "email": "shipper@example.com",
  "role": "SHIPPER",
  "status": "ACTIVE",
  "last_login_at": "2026-02-04T12:00:00Z",
  "created_at": "2026-02-04T10:00:00Z"
}
```

### 4. Refresh Token

Refresh the access token using the refresh token.

```bash
curl -X POST http://localhost:10000/api/v1/auth/refresh \
  -H "Cookie: refresh_token=your_refresh_token"
```

**Success Response (200):**
```json
{
  "message": "Token refreshed successfully"
}
```

### 5. Logout

Log out and clear authentication cookies.

```bash
curl -X POST http://localhost:10000/api/v1/auth/logout \
  -H "Cookie: access_token=your_jwt_token"
```

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

## User Roles

The system supports four user roles:

1. **SHIPPER** - Companies or individuals shipping goods
2. **CARRIER_OWNER** - Truck/fleet owners
3. **DRIVER** - Individual drivers
4. **ADMIN** - System administrators

## Role-Based Access Control

Use the `require_role` dependency to protect endpoints:

```python
from app.api.deps import require_role

@router.get("/admin-only")
async def admin_endpoint(
    current_user = Depends(require_role(["ADMIN"]))
):
    return {"message": "Admin content"}

# Multiple roles
@router.get("/logistics")
async def logistics_endpoint(
    current_user = Depends(require_role(["SHIPPER", "CARRIER_OWNER", "ADMIN"]))
):
    return {"message": "Logistics content"}
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/
```

## Database Schema

### Users Table
- `id` (UUID, Primary Key)
- `email` (VARCHAR, Unique, Indexed)
- `password_hash` (VARCHAR) - Bcrypt hashed
- `role` (ENUM: SHIPPER, CARRIER_OWNER, DRIVER, ADMIN)
- `status` (ENUM: ACTIVE, SUSPENDED)
- `failed_login_attempts` (INTEGER, default: 0)
- `locked_until` (TIMESTAMPTZ, nullable)
- `last_login_at` (TIMESTAMPTZ, nullable)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

### Audit Logs Table
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key, Nullable)
- `action` (VARCHAR, Indexed) - e.g., USER_REGISTERED, USER_LOGIN
- `ip_address` (VARCHAR, Nullable)
- `user_agent` (TEXT, Nullable)
- `metadata` (JSONB, Nullable)
- `created_at` (TIMESTAMPTZ, Indexed)

## Audit Events

The following events are automatically logged:

- `USER_REGISTERED` - New user registration
- `USER_LOGIN` - Successful login
- `USER_FAILED_LOGIN` - Failed login attempt
- `USER_LOCKED` - Account locked after failed attempts
- `USER_LOGOUT` - User logout

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key (generate with `openssl rand -hex 32`) | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration time | 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration (remember_me) | 30 |
| `ENVIRONMENT` | Environment mode (development/production) | development |
| `CORS_ORIGINS` | Allowed CORS origins | ["http://localhost:3000"] |

## Password Requirements

Passwords must meet all requirements:
- Minimum 8 characters
- At least 1 uppercase letter (A-Z)
- At least 1 lowercase letter (a-z)
- At least 1 number (0-9)

## 🔧 Troubleshooting

### Database Connection Issues

**Error: Connection refused**
```bash
# Check if Supabase project is active
# Dashboard > Settings > Database > Status should be "Healthy"

# Verify connection string in .env
cat .env | grep DATABASE_URL
```

**Error: Password authentication failed**
```bash
# Reset database password in Supabase
# Dashboard > Settings > Database > Reset database password
```

**Error: Tables don't exist**
```bash
# Run migrations
alembic upgrade head --verbose

# Or use test script
python test_connection.py
```

### Migration Errors

```bash
# Reset migrations (WARNING: This deletes all data)
alembic downgrade base
alembic upgrade head

# Or migrate with verbose output
alembic upgrade head --verbose
```

### Token Issues

**Error: Invalid token**
- Verify SECRET_KEY is set and consistent
- Check token expiration times in config
- Ensure cookies are being sent with requests

### CORS Errors

```bash
# Update CORS_ORIGINS in .env
CORS_ORIGINS=["http://localhost:3000","http://localhost:10000"]
# Restart server after changes
```

### Supabase-Specific Issues

**Error: SSL connection required**
- Supabase requires SSL connections
- Connection string should be: `postgresql+asyncpg://...`
- NOT `postgresqls://...`

**Error: Too many connections**
- Supabase free tier has connection limits
- Use connection pooling (already configured)
- Consider upgrading for production

## 📦 Additional Resources

### Setup Guides
- **Supabase Setup**: [`SUPABASE_SETUP.md`](SUPABASE_SETUP.md) - Complete Supabase configuration
- **Swagger Guide**: [`SWAGGER_GUIDE.md`](SWAGGER_GUIDE.md) - Interactive API documentation

### Setup Scripts
- **Linux/macOS**: `setup_supabase.sh` - Automated setup script
- **Windows**: `setup_supabase.bat` - Windows batch script
- **Test Script**: `test_connection.py` - Verify database connection

## Account Lockout

Security mechanism to prevent brute force attacks:
- After 5 consecutive failed login attempts
- Account locked for 30 minutes
- Lock expiration time tracked in database
- All failures logged with IP address

## Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Generate a strong `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Enable HTTPS and set `secure=True` for cookies
- [ ] Set proper `CORS_ORIGINS` for your frontend domain
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall to allow only port 10000
- [ ] Set up log monitoring
- [ ] Configure database backups
- [ ] Set up monitoring and alerting
- [ ] Review and test all security features

## Troubleshooting

### Migration Errors
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### Database Connection Issues
- Verify PostgreSQL is running: `docker ps` or `pg_isready`
- Check DATABASE_URL format
- Ensure database exists

### Token Issues
- Verify SECRET_KEY is set and consistent
- Check token expiration times
- Ensure cookies are being sent with requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check API documentation at `/docs`
- Review audit logs for security events

## Security

If you discover a security vulnerability, please email security@yourcompany.com instead of creating a public issue.

---

**Built with ❤️ for secure B2B freight marketplace authentication**
