import getpass
import json
import os
import tempfile

from src.auth import TEACHERS_FILE, hash_password


def main() -> None:
    username = input("Teacher username: ").strip()
    if not username or len(username) > 128:
        raise SystemExit("Username must contain between 1 and 128 characters.")

    password = getpass.getpass("Teacher password (at least 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if len(password) > 1024:
        raise SystemExit("Password must contain no more than 1024 characters.")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")

    teachers = {}
    if TEACHERS_FILE.exists():
        try:
            data = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit("Teacher credentials file contains invalid JSON.") from error
        if not isinstance(data, dict) or not isinstance(data.get("teachers"), dict):
            raise SystemExit("Teacher credentials file has an invalid format.")
        teachers = data["teachers"]

    if username in teachers and input(
        f"Replace credentials for {username}? [y/N] "
    ).strip().lower() != "y":
        raise SystemExit("No changes made.")

    teachers[username] = hash_password(password)
    TEACHERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=TEACHERS_FILE.parent,
            delete=False,
        ) as credentials_file:
            temporary_path = credentials_file.name
            os.chmod(temporary_path, 0o600)
            json.dump({"teachers": teachers}, credentials_file, indent=2)
            credentials_file.write("\n")
            credentials_file.flush()
            os.fsync(credentials_file.fileno())
        os.replace(temporary_path, TEACHERS_FILE)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)

    print(f"Credentials saved to {TEACHERS_FILE}.")


if __name__ == "__main__":
    main()
