# Mergington High School Activities API

A simple FastAPI application that lets visitors view extracurricular activities
and lets authenticated teachers manage student signups.

## Features

- View all available extracurricular activities
- Teacher login/logout and teacher-only signup management
- Salted PBKDF2-SHA256 password hashes stored in a local JSON file

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Create a teacher account. The password is prompted securely and is never
   saved in plaintext:

   ```
   python -m src.create_teacher
   ```

   The command creates `teachers.json` in the repository root with restricted
   file permissions. This local file is ignored by Git. Run the command again
   to add or replace a teacher account.

3. Set a persistent session signing key before deployment:

   ```
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

   In production, set `APP_ENV=production` and serve over HTTPS. Production
   requires `SESSION_SECRET` and marks the session cookie secure.

4. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

5. Open http://localhost:8000. Visitors can view activities; teachers can sign
   in using the account created above to manage signups. The API also enforces
   teacher authentication on signup and unregister requests, so hiding the
   controls in the browser is not the security boundary.

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | View activities and current participants |
| GET | `/auth/session` | Check the current login status |
| POST | `/auth/login` | Sign in with a teacher username and password |
| POST | `/auth/logout` | Sign out |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only signup |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only unregister |

Activities remain in memory and reset when the server restarts.
