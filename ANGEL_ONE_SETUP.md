# Angel One SmartAPI — local setup

This project uses the SmartAPI login endpoint directly over HTTPS for the initial
authentication milestone. It intentionally does not use the SDK's default
logging path, because some SDK error paths can write request headers and request
parameters to logs.

## 1. Create the local secrets file

Create a folder named `.streamlit` in the project root. Copy
`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.

Fill these values locally:

- `R77Z2USYVIXTN6LZLWCFBDNQRU`: API key from your SmartAPI app.
- `N296645`: your Angel One client code.
- `1991`: your Angel One login PIN.

Never commit the real `.streamlit/secrets.toml` file. It is ignored by
`.gitignore`. Do not paste credentials or OTPs into GitHub issues, pull
requests, source files, screenshots, or chat.

## 2. Start the dashboard

```bash
pip install -r requirements.txt
streamlit run app.py
```

In the sidebar, enter the current 6-digit TOTP from your authenticator and
press **Connect to Angel One**. The TOTP is submitted for login only and is not
written to the secrets file or retained by the auth client.

The app validates the login by calling the protected SmartAPI profile endpoint.
It displays only a masked client code and connection status; it does not display
the profile payload or tokens.

## 3. Network identity

SmartAPI requests include its documented client network headers. The app detects
the local IPv4 and MAC address, and discovers the public IPv4 using
`https://api.ipify.org` (only the public IP is sent to that service). If that
lookup is blocked, set `ANGELONE_CLIENT_PUBLIC_IP` in your local secrets file.

## 4. Session handling

JWT, refresh and feed tokens are held only in the running Streamlit process
memory. They are not written to disk, logs, cache, or Git. The app has no order
placement code. Disconnect requests broker logout and clears local tokens.

SmartAPI sessions may end at midnight or earlier. Reconnect with a fresh TOTP
when required. This implementation's token refresh is provided for the next
market-data phase; it should not be used to keep a session open across broker
session expiry.

## 5. Scope

This milestone verifies account authentication and the protected profile call.
Historical candles, instrument-token mapping, WebSocket streaming, and live
sector data are separate follow-on milestones. The existing dashboard's Yahoo
prototype feed remains the displayed market-data source until those features
are implemented and tested.
