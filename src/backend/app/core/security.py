"""비밀번호 암호화와 세션 토큰.

비밀번호는 파이썬 기본 라이브러리의 scrypt로 암호화한다(추가 패키지 없음).
저장 형식: scrypt$N$r$p$소금(hex)$해시(hex)
"""

import hashlib
import hmac
import re
import secrets
import string
from datetime import datetime, timezone

_N, _R, _P, _DKLEN = 2**14, 8, 1, 64

# 비밀번호 규칙: 8자 이상, 영문·숫자 포함 (API 설계서 5장 임시 비밀번호 규칙과 같음)
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# 로그인할 수 없는 비밀번호 값. '삭제된 사용자'로 바꿀 때 password_hash에 넣는다.
UNUSABLE_PASSWORD = "!"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False  # UNUSABLE_PASSWORD 등
    if algo != "scrypt":
        return False
    digest = hashlib.scrypt(
        password.encode(),
        salt=bytes.fromhex(salt_hex),
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=len(digest_hex) // 2,
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def is_valid_password(password: str) -> bool:
    return (
        PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH
        and re.search(r"[A-Za-z]", password) is not None
        and re.search(r"[0-9]", password) is not None
    )


def generate_temporary_password(length: int = 12) -> str:
    """규칙(영문·숫자 포함)을 만족하는 임시 비밀번호."""
    alphabet = string.ascii_letters + string.digits
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if is_valid_password(pw):
            return pw


def new_session_token() -> str:
    """쿠키에 담을 랜덤 토큰. DB에는 hash_token() 값만 저장한다."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
