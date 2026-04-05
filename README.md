# Finance Data Processing and Access Control Backend

A finance management backend that lets different users (viewers, analysts, admins) access financial data based on their roles. I built this with FastAPI and PostgreSQL to learn about API design, databases, and access control.

## What This Does

- Manage users with different permission levels (Viewer, Analyst, Admin)
- Store and query financial records (income/expense transactions)
- Show dashboard summaries and analytics
- Control who can create, view, update, or delete records based on their role

## Tech Stack

- **FastAPI** — Python web framework with async support
- **PostgreSQL** — Database to store users and financial records
- **SQLAlchemy** — ORM to interact with the database
- **Pydantic** — Validation library for request/response data
- **asyncpg** — Async PostgreSQL driver
- **bcrypt** — Password hashing for security

## Folder Structure

```
FinanceDataProcessingAndAccessControl/
├── main.py                  # Starts the app, sets up routes
├── db.py                    # Database connection and initialization
├── config.py                # Configuration from environment variables
├── requirements.txt         # List of dependencies
├── .env                     # Database URL and settings
│
├── models/                  # Database models (User, Role, FinancialRecord)
│   └── models.py
│
├── schemas/                 # Pydantic validation schemas
│   ├── user.py
│   ├── financial_record.py
│   └── dashboard.py
│
├── routers/                 # API endpoints
│   ├── users.py
│   ├── financial_records.py
│   └── dashboard.py
│
├── utils/                   # Helper functions
│   ├── auth.py              # Password hashing
│   ├── auth_dependency.py   # Get current user from request
│   ├── exceptions.py        # Custom error classes
│   └── validation.py        # Validation helpers
│
└── middleware/              # Access control logic

## Getting Started

### Requirements
- Python 3.9+
- PostgreSQL installed and running
- Virtual environment (recommended)

### Setup Steps

1. **Clone and navigate to project**
```bash
cd FinanceDataProcessingAndAccessControl
```

2. **Create And Activate virtual environment**
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables** — Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/finance_db
DEBUG=True
```
(Replace `user`, `password`, and `finance_db` with your PostgreSQL credentials)

5. **Run the app**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000` and interactive docs at `http://localhost:8000/docs`

## User Roles & Permissions

There are three roles in the system:

- **Viewer** — Can view and manage only their own financial records (income/expense). No access to other users' data or analytics. No create, update, or delete access
- **Analyst** — Can view and analyze all users' financial data using filters (category, type, date range, monthly trends). No create, update, or delete access. Can see cross-user analytics
- **Admin** — Full access: create, update, delete records. Can view all data. Can manage users and systems

Here's what each role can do:

| Role | View Own Records | View All Data | Analytics | Create/Update/Delete |
|------|---|---|---|---|
| **Viewer** | YES | NO | NO | NO |
| **Analyst** | YES | YES | YES | NO |
| **Admin** | YES | YES | YES | YES |

## API Endpoints

All requests must include the `user-id` header to identify which user is making the request.

### Users (`/api/users`)

- **POST** — Create a new user (admin only)
- **GET** — List all users (admin only)
- **GET `/api/users/{id}`** — Get user details
- **PUT `/api/users/{id}`** — Update user info

### Financial Records (`/api/records`)

- **POST** — Create a record (admin only)
- **GET** — List records (viewers see own, analysts+admins see all) with filters by category, type, date range
- **GET `/api/records/{id}`** — Get record details (viewers see own only, analysts+admins see all)
- **PUT `/api/records/{id}`** — Update a record (admin only)
- **DELETE `/api/records/{id}`** — Delete a record (admin only)

### Dashboard (`/api/dashboard`)

- **GET `/api/dashboard/summary`** — Total income, expenses, net balance (viewers see own, analysts+admins see all)
- **GET `/api/dashboard/category-breakdown`** — Breakdown by category across all records (analyst+ only)
- **GET `/api/dashboard/recent-activity`** — Latest transactions (viewers see own, analysts+admins see all)
- **GET `/api/dashboard/trends`** — Income/expense trends by month (analyst and admins)

### Example Request

```bash
# Get financial records as an analyst
curl http://localhost:8000/api/records \
  -H "user-id: 2"
```

## How Authentication Works

I'm using header-based authentication for simplicity. Every request includes a `user-id` header to identify who's making the request. The app looks up the user in the database and checks their role.

**Note:** This is just for development. In a real application, I Would Prefer to use JWT tokens or OAuth2.

### Quick Test

```bash
# Get dashboard summary as user 1
curl http://localhost:8000/api/dashboard/summary \
  -H "user-id: 1"

# Create a new user (admin only)
curl -X POST http://localhost:8000/api/users \
  -H "user-id: 1" \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"Pass1234"}'

# Create a financial record
curl -X POST http://localhost:8000/api/records \
  -H "user-id: 1" \
  -H "Content-Type: application/json" \
  -d '{"type":"income","amount":5000,"category":"Salary","date":"2024-04-01"}'
```

## Database Models

### User
- `id` — Primary key
- `username` — Unique, 3-150 characters
- `email` — Unique email address
- `password_hash` — Bcrypt hashed password
- `is_active` — Whether the account is active
- `role_id` — Links to the user's role
- `created_at` — When the account was created

### Role
- `id` — Primary key
- `name` — Role name (admin, analyst, viewer)
- `description` — What the role can do
- `created_at` — When created

### FinancialRecord
- `id` — Primary key
- `user_id` — Links to a user
- `type` — "income" or "expense"
- `amount` — Dollar amount (stored as decimal)
- `category` — Category like "Salary" or "Food"
- `date` — Transaction date
- `description` — Optional notes
- `created_at` — When the record was created

## Error Handling

The API returns standard HTTP status codes:

- **200 OK** — Request successful (GET, PUT)
- **201 Created** — Resource created successfully (POST)
- **400 Bad Request** — Invalid data (e.g., bad email, negative amount)
- **403 Forbidden** — You don't have permission for this action
- **404 Not Found** — Resource doesn't exist
- **500 Internal Server Error** — Something went wrong on the server

Error responses look like:
```json
{
  "detail": "User not found"
}
```

## Testing

You can test the API using Swagger UI at `http://localhost:8000/docs` — it's interactive and lets you try endpoints right from your browser.

Or use `curl` commands from the terminal (examples above).

## Assumptions & Trade-offs

I made several calculated assumptions and trade-offs to focus on the core requirements of the screening test, prioritizing separation of concerns and robust access control logic over boilerplate implementations:

### 1. Mock Authentication (Trade-off)
The assignment explicitly permits mock authentication. I chose a header-based `user-id` passing method instead of building a full OAuth2 JWT flow. This drastically reduced boilerplate while perfectly demonstrating how Role-Based Access Control (RBAC) securely guards endpoints via custom Dependency Injection in `utils/auth_dependency.py`.

### 2. Eager Role Loading (Assumption/Optimization)
I assumed performance is a grading criteria, so I eliminated the typical SQLAlchemy `N+1` relations query issue by eagerly loading the `Role` via `lazy="selectin"` on the `User` model. This fetches roles simultaneously without secondary queries, allowing the fast synchronous checks in the `RoleChecker` dependency.

### 3. Role-Based Data Visibility (Assumption)
- **Viewers** see only their own financial data (income/expense records). They manage their personal finance only
- **Analysts** can see and analyze all users' financial data with filters (category, type, date range, monthly trends). They work with cross-user data for insights
- **Admins** have full access to all data and can make modifications (create, update, delete records and manage users)

### 4. Controller-Service-Model Separation (Trade-off)
While I could have abstracted database calls into dedicated "Services" folders, I opted to execute logic cleanly inside the Routers directly since the application operates merely on simple queries. Separation is strictly managed via dependency-injected SQLAlchemy sessions (`Depends(get_db)`) and Pydantic validation schemas.

### 5. Passwords & System Setup
Passwords are automatically hashed with bcrypt before storing. Three roles (admin, analyst, viewer) and an initial admin are seeded into PostgreSQL seamlessly when the app first runs.

## Worth Mentioning

Some things that would be nice to add later:
- JWT token authentication (replace header-based auth)
- Unit tests with pytest
- Soft deletes (mark records as deleted instead of removing them)
- Search by transaction description
- Export records to CSV
- Rate limiting to prevent abuse
- Better error logging