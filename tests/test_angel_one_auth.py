from dataclasses import fields

import pytest

from src.data.angel_one.auth import (
    AngelOneAuthError,
    AngelOneSmartAPI,
    SessionTokens,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            error = requests.HTTPError("HTTP failure")
            error.response = self
            raise error

    def json(self):
        return self._payload


class FakeHTTP:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def identity_provider(_public_ip):
    return {
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP": "203.0.113.10",
        "X-MACAddress": "00:11:22:33:44:55",
    }


def successful_login():
    return {
        "status": True,
        "message": "SUCCESS",
        "data": {
            "jwtToken": "jwt-secret",
            "refreshToken": "refresh-secret",
            "feedToken": "feed-secret",
        },
    }


def successful_profile():
    return {
        "status": True,
        "message": "SUCCESS",
        "data": {"clientcode": "TEST123", "exchanges": ["NSE"]},
    }


def make_client(http):
    return AngelOneSmartAPI(
        "api-key-secret",
        "TEST123",
        public_ip="203.0.113.10",
        http=http,
        identity_provider=identity_provider,
    )


def test_login_posts_credentials_then_checks_profile():
    http = FakeHTTP([
        FakeResponse(successful_login()),
        FakeResponse(successful_profile()),
    ])
    client = make_client(http)

    profile = client.login("pin-secret", "123456")

    assert profile["data"]["clientcode"] == "TEST123"
    assert client.is_authenticated is True
    assert http.calls[0]["json"] == {
        "clientcode": "TEST123",
        "password": "pin-secret",
        "totp": "123456",
    }
    assert http.calls[0]["verify"] is True
    assert http.calls[1]["headers"]["Authorization"] == "Bearer jwt-secret"
    assert "api-key-secret" not in repr(client)
    assert "jwt-secret" not in repr(client)


def test_invalid_totp_is_rejected_without_network_call():
    http = FakeHTTP([])
    client = make_client(http)

    with pytest.raises(AngelOneAuthError, match="6-digit"):
        client.login("pin-secret", "12345")

    assert http.calls == []


def test_failed_profile_check_discards_issued_tokens():
    http = FakeHTTP([
        FakeResponse(successful_login()),
        FakeResponse({"status": False, "message": "Invalid Auth Token", "errorcode": "AB1011"}),
    ])
    client = make_client(http)

    with pytest.raises(AngelOneAuthError, match="profile check"):
        client.login("pin-secret", "123456")

    assert client.is_authenticated is False


def test_refresh_replaces_all_tokens():
    http = FakeHTTP([
        FakeResponse(successful_login()),
        FakeResponse(successful_profile()),
        FakeResponse({
            "status": True,
            "data": {
                "jwtToken": "new-jwt",
                "refreshToken": "new-refresh",
                "feedToken": "new-feed",
            },
        }),
    ])
    client = make_client(http)
    client.login("pin-secret", "123456")
    client.refresh_tokens()

    assert http.calls[2]["json"] == {"refreshToken": "refresh-secret"}
    assert http.calls[2]["headers"]["Authorization"] == "Bearer jwt-secret"
    assert client.is_authenticated


def test_session_token_values_are_excluded_from_dataclass_repr():
    tokens = SessionTokens("jwt-secret", "refresh-secret", "feed-secret")

    assert "jwt-secret" not in repr(tokens)
    assert "refresh-secret" not in repr(tokens)
    assert "feed-secret" not in repr(tokens)
    assert all(item.repr is False for item in fields(SessionTokens))
