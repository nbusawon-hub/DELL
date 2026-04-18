# Hotmail/Outlook Connection Setup

Microsoft has **disabled basic authentication** (username + password) for IMAP/SMTP
on both business M365 accounts (October 2022) and personal Hotmail/Outlook.com
accounts (September 2024). You now have to use **OAuth 2.0** via the
**Microsoft Graph API**. This project uses the **device code flow**, so you
don't need a redirect URI or client secret.

## 1. Register an application in Microsoft Entra

1. Go to <https://entra.microsoft.com> (or <https://portal.azure.com>) and sign
   in with a Microsoft account.
2. Navigate to **Microsoft Entra ID** → **App registrations** → **New
   registration**.
3. Fill in:
   - **Name**: `hotmail-client` (or anything you like)
   - **Supported account types**: *Accounts in any organizational directory and
     personal Microsoft accounts* (this is what lets you sign in with a
     `@hotmail.com` or `@outlook.com` address)
   - **Redirect URI**: leave blank
4. Click **Register**. On the Overview page, copy the **Application (client)
   ID**.

## 2. Enable public client flows

Device code flow is a *public client* flow — it doesn't use a secret.

1. In your app registration, go to **Authentication**.
2. Scroll down to **Allow public client flows** and set it to **Yes**.
3. Click **Save**.

## 3. Add Microsoft Graph permissions

1. Go to **API permissions** → **Add a permission** → **Microsoft Graph** →
   **Delegated permissions**.
2. Add:
   - `User.Read`
   - `Mail.Read`
   - `Mail.Send`
   - `offline_access` (for refresh tokens)
3. Click **Add permissions**. Admin consent is *not* required for these
   delegated scopes on a personal account.

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure the client

Either set an env var:

```bash
export AZURE_CLIENT_ID="<the client ID from step 1>"
# optional; defaults to "common" which works for personal accounts
export AZURE_TENANT_ID="common"
```

Or copy the example config:

```bash
cp config.cfg.example config.cfg
# then edit config.cfg and paste your Client ID
```

## 6. Run the client

```bash
python hotmail_client.py
```

On first run you'll see something like:

```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABCD1234 to authenticate.
```

Open that URL on any device, enter the code, and sign in with your Hotmail
account. The script will then print your recent inbox.
