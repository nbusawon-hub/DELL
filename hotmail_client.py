"""
Hotmail/Outlook Email Client using Microsoft Graph API.

Basic auth (username/password) for IMAP/SMTP has been disabled by Microsoft.
This client uses Microsoft Graph with OAuth 2.0 device code flow, which works
for personal Hotmail/Outlook.com accounts as well as work/school accounts.

Setup: see SETUP.md for registering an Entra app and getting a Client ID.
"""

import asyncio
import configparser
import os
from pathlib import Path

from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.users.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)


SCOPES = ["User.Read", "Mail.Read", "Mail.Send"]


class HotmailGraphClient:
    def __init__(self, client_id, tenant_id="common"):
        self.credential = DeviceCodeCredential(
            client_id=client_id,
            tenant_id=tenant_id,
        )
        self.client = GraphServiceClient(
            credentials=self.credential,
            scopes=SCOPES,
        )

    async def get_user(self):
        """Return the signed-in user's profile."""
        return await self.client.me.get()

    async def list_inbox(self, top=10):
        """Return the most recent messages from the inbox."""
        query = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            select=["from", "isRead", "receivedDateTime", "subject"],
            top=top,
            orderby=["receivedDateTime DESC"],
        )
        config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query,
        )
        result = await self.client.me.mail_folders.by_mail_folder_id(
            "inbox"
        ).messages.get(request_configuration=config)
        return result.value if result else []

    async def send_mail(self, subject, body, to_address, html=False):
        """Send an email from the signed-in user."""
        message = Message(
            subject=subject,
            body=ItemBody(
                content_type=BodyType.Html if html else BodyType.Text,
                content=body,
            ),
            to_recipients=[
                Recipient(email_address=EmailAddress(address=to_address)),
            ],
        )
        request = SendMailPostRequestBody(message=message, save_to_sent_items=True)
        await self.client.me.send_mail.post(request)


def load_config():
    """Load client_id / tenant_id from env vars or config.cfg."""
    client_id = os.environ.get("AZURE_CLIENT_ID")
    tenant_id = os.environ.get("AZURE_TENANT_ID", "common")

    if not client_id:
        cfg_path = Path(__file__).with_name("config.cfg")
        if cfg_path.exists():
            parser = configparser.ConfigParser()
            parser.read(cfg_path)
            client_id = parser.get("azure", "clientId", fallback=None)
            tenant_id = parser.get("azure", "tenantId", fallback=tenant_id)

    if not client_id:
        raise SystemExit(
            "Missing Azure client ID. Set AZURE_CLIENT_ID env var or "
            "create config.cfg (see SETUP.md)."
        )
    return client_id, tenant_id


async def main():
    client_id, tenant_id = load_config()
    client = HotmailGraphClient(client_id, tenant_id)

    user = await client.get_user()
    print(f"Signed in as: {user.display_name} <{user.mail or user.user_principal_name}>")

    print("\n--- Recent Inbox ---")
    messages = await client.list_inbox(top=5)
    for m in messages:
        sender = m.from_.email_address.address if m.from_ and m.from_.email_address else "?"
        flag = " " if m.is_read else "*"
        print(f"{flag} {m.received_date_time}  {sender}")
        print(f"    {m.subject}")


if __name__ == "__main__":
    asyncio.run(main())
