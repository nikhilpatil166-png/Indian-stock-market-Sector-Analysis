"""Minimal, security-conscious Angel One SmartAPI authentication client.

This module intentionally implements only login, profile verification, token
refresh, and logout. It does not contain any order-placement functionality.
"""

from __future__ import annotations

import ipaddress
import socket
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

import requests


ROOT_URL = "https://apiconnect.angelone.in"
LOGIN_PATH = "/rest/auth/angelbroking/user/v1/loginByPassword"
PROFILE_PATH = "/rest/secure/angelbroking/user/v1/getProfile"
TOKEN_PATH = "/rest/auth/angelbroking/jwt/v1/generateTokens"
LOGOUT_PATH = "/rest/secure/angelbroking/user/v1/logout"
REQUEST_TIMEOUT_SECONDS = 15


class AngelOneAuthError(RuntimeError):
    """Safe, user-facing SmartAPI authentication or connection error."""


@dataclass(frozen=True)
class SessionTokens:
    """In-memory SmartAPI session material; values are omitted from repr()."""

    jwt_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    feed_token: str = field(repr=False)


def _local_ipv4() -> str:
    """Find the outbound local IPv4 without sending application data."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        address = sock.getsockname()[0]
        return str(ipaddress.ip_address(address))
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def _public_ipv4() -> str:
    """Resolve the public IPv4 used in SmartAPI headers; no secrets are sent."""
    try:
        response = requests.get("https://api.ipify.org", timeout=4)
        response.raise_for_status()
        address = str(ipaddress.ip_address(response.text.strip()))
        if ":" in address:
            raise ValueError("IPv6 address returned; IPv4 is required here.")
        return address
    except Exception as exc:
        raise AngelOneAuthError(
            "Could not detect your public IPv4 address. Set "
            "ANGELONE_CLIENT_PUBLIC_IP in your local Streamlit secrets file "
            "and try again."
        ) from exc


def _network_identity(public_ip_override: str | None = None) -> dict[str, str]:
    public_ip = public_ip_override.strip() if public_ip_override else _public_ipv4()
    try:
        parsed_public_ip = ipaddress.ip_address(public_ip)
    except ValueError as exc:
        raise AngelOneAuthError(
            "ANGELONE_CLIENT_PUBLIC_IP must be a valid IP address."
        ) from exc
    if parsed_public_ip.version != 4:
        raise AngelOneAuthError("ANGELONE_CLIENT_PUBLIC_IP must be IPv4.")

    mac_value = uuid.getnode()
    mac_address = ":".join(
        f"{(mac_value >> shift) & 0xff:02x}" for shift in range(40, -1, -8)
    )
    return {
        "X-ClientLocalIP": _local_ipv4(),
        "X-ClientPublicIP": public_ip,
        "X-MACAddress": mac_address,
    }


class AngelOneSmartAPI:
    """Small REST client for SmartAPI session management."""

    def __init__(
        self,
        api_key: str,
        client_code: str,
        *,
        public_ip: str | None = None,
        http: Any | None = None,
        identity_provider: Callable[[str | None], dict[str, str]] = _network_identity,
    ) -> None:
        if not api_key or not api_key.strip():
            raise AngelOneAuthError("Angel One API key is missing.")
        if not client_code or not client_code.strip():
            raise AngelOneAuthError("Angel One client code is missing.")

        self._api_key = api_key.strip()
        self._client_code = client_code.strip()
        self._public_ip = public_ip
        self._http = http or requests.Session()
        self._identity_provider = identity_provider
        self._tokens: SessionTokens | None = None

    @property
    def is_authenticated(self) -> bool:
        return self._tokens is not None

    def _headers(self, *, authenticated: bool = False) -> dict[str, str]:
        identity = self._identity_provider(self._public_ip)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-PrivateKey": self._api_key,
            **identity,
        }
        if authenticated:
            if self._tokens is None:
                raise AngelOneAuthError("Connect to Angel One first.")
            headers["Authorization"] = f"Bearer {self._tokens.jwt_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        authenticated: bool = False,
        operation: str,
    ) -> dict[str, Any]:
        try:
            response = self._http.request(
                method=method,
                url=f"{ROOT_URL}{path}",
                json=payload,
                headers=self._headers(authenticated=authenticated),
                timeout=REQUEST_TIMEOUT_SECONDS,
                verify=True,
            )
            response.raise_for_status()
            body = response.json()
        except requests.Timeout as exc:
            raise AngelOneAuthError(
                f"Angel One {operation} timed out. Check your network and retry."
            ) from exc
        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            suffix = f" (HTTP {status})" if status else ""
            raise AngelOneAuthError(
                f"Could not complete Angel One {operation}{suffix}. "
                "Check connectivity and SmartAPI status."
            ) from exc
        except ValueError as exc:
            raise AngelOneAuthError(
                f"Angel One returned an unreadable response during {operation}."
            ) from exc

        if not isinstance(body, dict):
            raise AngelOneAuthError(
                f"Angel One returned an unexpected response during {operation}."
            )
        if body.get("status") is not True:
            code = body.get("errorcode") or "not supplied"
            message = body.get("message") or "Request rejected"
            raise AngelOneAuthError(
                f"Angel One {operation} failed: {message} (code: {code})."
            )
        return body

    @staticmethod
    def _tokens_from_response(body: dict[str, Any]) -> SessionTokens:
        data = body.get("data") or {}
        jwt_token = data.get("jwtToken")
        refresh_token = data.get("refreshToken")
        feed_token = data.get("feedToken")
        if not all(isinstance(value, str) and value for value in (
            jwt_token, refresh_token, feed_token
        )):
            raise AngelOneAuthError(
                "SmartAPI login response did not contain all required session tokens."
            )
        return SessionTokens(
            jwt_token=jwt_token,
            refresh_token=refresh_token,
            feed_token=feed_token,
        )

    def login(self, pin: str, totp: str) -> dict[str, Any]:
        """Login with client code, PIN and the current 6-digit TOTP.

        Returns the profile response after validating the new bearer token.
        TOTP is not saved on the client object or written to disk.
        """
        cleaned_totp = str(totp).strip()
        if not cleaned_totp.isdigit() or len(cleaned_totp) != 6:
            raise AngelOneAuthError("Enter the current 6-digit authenticator code.")
        if not pin or not str(pin).strip():
            raise AngelOneAuthError("Angel One PIN is missing.")

        body = self._request(
            "POST",
            LOGIN_PATH,
            payload={
                "clientcode": self._client_code,
                "password": str(pin).strip(),
                "totp": cleaned_totp,
            },
            authenticated=False,
            operation="login",
        )
        self._tokens = self._tokens_from_response(body)

        # Verify that the newly issued JWT is accepted by a protected endpoint.
        try:
            return self.get_profile()
        except AngelOneAuthError:
            self._tokens = None
            raise

    def get_profile(self) -> dict[str, Any]:
        """Call the protected profile endpoint to verify the session."""
        return self._request(
            "GET",
            PROFILE_PATH,
            authenticated=True,
            operation="profile check",
        )

    def refresh_tokens(self) -> None:
        """Replace in-memory JWT, refresh and feed tokens using the refresh token."""
        if self._tokens is None:
            raise AngelOneAuthError("Connect to Angel One before refreshing tokens.")

        # SmartAPI's documented token endpoint accepts the refresh token in JSON
        # and the current JWT in Authorization.
        body = self._request(
            "POST",
            TOKEN_PATH,
            payload={"refreshToken": self._tokens.refresh_token},
            authenticated=True,
            operation="token refresh",
        )
        self._tokens = self._tokens_from_response(body)

    def logout(self) -> None:
        """Request broker logout, then always discard local session tokens."""
        if self._tokens is None:
            return
        try:
            self._request(
                "POST",
                LOGOUT_PATH,
                payload={"clientcode": self._client_code},
                authenticated=True,
                operation="logout",
            )
        finally:
            self._tokens = None
