import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt-hashed password (utf-8 string)."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Returns False for non-hash inputs (legacy plaintext) if they don't match.
    """
    if not isinstance(hashed, str):
        return False
    if hashed.startswith('$2'):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    # legacy plaintext fallback
    return password == hashed
