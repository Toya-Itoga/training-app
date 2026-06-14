"""Tests for authentication service: token creation, verification, password hashing."""
import pytest

from utils.auth import create_token, decode_token
from services.auth_service import hash_password, verify_password


class TestTokens:
    def test_create_and_decode(self):
        token = create_token("user123", "tanaka")
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "tanaka"

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("bad.token.value")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises(self):
        from fastapi import HTTPException
        token = create_token("user123", "tanaka")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException):
            decode_token(tampered)


class TestPasswords:
    def test_hash_and_verify(self):
        hashed = hash_password("StrongPass1!")
        assert verify_password("StrongPass1!", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_not_plaintext(self):
        pw = "secret123"
        hashed = hash_password(pw)
        assert pw not in hashed
        assert len(hashed) > 20
