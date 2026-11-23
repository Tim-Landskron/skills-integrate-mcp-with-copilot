import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any


PBKDF2_ITERATIONS = 600_000
MIN_PBKDF2_ITERATIONS = 100_000
MAX_PBKDF2_ITERATIONS = 2_000_000
TEACHERS_FILE = Path(
    os.environ.get(
        "TEACHERS_FILE",
        Path(__file__).resolve().parent.parent / "teachers.json",
    )
)


def hash_password(password: str) -> dict[str, Any]:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return {
        "algorithm": "pbkdf2_sha256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": salt.hex(),
        "password_hash": password_hash.hex(),
    }


def _password_material(credential: dict[str, Any]) -> tuple[int, bytes, bytes]:
    if credential.get("algorithm") != "pbkdf2_sha256":
        raise ValueError("Unsupported password hashing algorithm")

    iterations = credential.get("iterations")
    if (
        not isinstance(iterations, int)
        or isinstance(iterations, bool)
        or not MIN_PBKDF2_ITERATIONS <= iterations <= MAX_PBKDF2_ITERATIONS
    ):
        raise ValueError("Invalid password hashing iteration count")

    try:
        salt = bytes.fromhex(credential["salt"])
        expected_hash = bytes.fromhex(credential["password_hash"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid password credential format") from error

    if len(salt) != 16 or len(expected_hash) != hashlib.sha256().digest_size:
        raise ValueError("Invalid password credential format")

    return iterations, salt, expected_hash


def verify_password(password: str, credential: dict[str, Any]) -> bool:
    iterations, salt, expected_hash = _password_material(credential)
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual_hash, expected_hash)


def load_teachers() -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(
            "Teacher credentials are not configured. "
            "Run `python src/create_teacher.py` to add a teacher."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Teacher credentials file contains invalid JSON") from error

    if not isinstance(data, dict) or not isinstance(data.get("teachers"), dict):
        raise RuntimeError("Teacher credentials file has an invalid format")

    for username, credential in data["teachers"].items():
        if not isinstance(username, str) or not isinstance(credential, dict):
            raise RuntimeError("Teacher credentials file has an invalid format")
        try:
            _password_material(credential)
        except ValueError as error:
            raise RuntimeError(
                f"Teacher credentials for {username!r} are invalid"
            ) from error

    return data["teachers"]
