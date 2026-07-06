from __future__ import annotations

from dataclasses import dataclass
import base64
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import requests

from .config import GraphConfig


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


@dataclass(frozen=True)
class MailAttachment:
    name: str
    content_type: str | None
    content: bytes


@dataclass(frozen=True)
class MailMessage:
    id: str
    subject: str | None
    received_date_time: str | None
    sender: str | None


class GraphClient:
    def __init__(self, config: GraphConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()
        self._access_token: str | None = None

    def list_candidate_messages(self, folder_name: str | None = None) -> list[MailMessage]:
        folder_id = self.resolve_folder_id(folder_name or self.config.source_folder)
        url = self._url(f"/users/{self._mailbox}/mailFolders/{folder_id}/messages")
        response = self._request(
            "GET",
            url,
            params={
                "$top": str(self.config.max_messages),
                "$filter": "hasAttachments eq true",
                "$select": "id,subject,receivedDateTime,from,hasAttachments",
            },
        )
        messages = [
            MailMessage(
                id=item["id"],
                subject=item.get("subject"),
                received_date_time=item.get("receivedDateTime"),
                sender=(
                    item.get("from", {})
                    .get("emailAddress", {})
                    .get("address")
                ),
            )
            for item in response.get("value", [])
        ]
        return [
            message
            for message in messages
            if self._subject_matches(message.subject)
        ]

    def list_pdf_attachments(self, message_id: str) -> list[MailAttachment]:
        url = self._url(f"/users/{self._mailbox}/messages/{quote(message_id)}/attachments")
        response = self._request("GET", url)
        attachments: list[MailAttachment] = []
        for item in response.get("value", []):
            if item.get("@odata.type") != "#microsoft.graph.fileAttachment":
                continue
            name = item.get("name") or "attachment.pdf"
            if not name.lower().endswith(".pdf"):
                continue
            content = item.get("contentBytes")
            if not content:
                continue
            attachments.append(
                MailAttachment(
                    name=name,
                    content_type=item.get("contentType"),
                    content=base64.b64decode(content),
                )
            )
        return attachments

    def get_message(self, message_id: str) -> MailMessage:
        url = self._url(f"/users/{self._mailbox}/messages/{quote(message_id)}")
        item = self._request(
            "GET",
            url,
            params={
                "$select": "id,subject,receivedDateTime,from,hasAttachments",
            },
        )
        return MailMessage(
            id=item["id"],
            subject=item.get("subject"),
            received_date_time=item.get("receivedDateTime"),
            sender=(
                item.get("from", {})
                .get("emailAddress", {})
                .get("address")
            ),
        )

    def move_message(self, message_id: str, destination_folder: str) -> None:
        folder_id = self.get_or_create_folder(destination_folder)
        url = self._url(f"/users/{self._mailbox}/messages/{quote(message_id)}/move")
        self._request("POST", url, json={"destinationId": folder_id})

    def create_message_subscription(
        self,
        notification_url: str,
        client_state: str,
        expiration_days: int = 6,
    ) -> dict[str, Any]:
        url = self._url("/subscriptions")
        expiration = datetime.now(timezone.utc) + timedelta(days=expiration_days)
        response = self._request(
            "POST",
            url,
            json={
                "changeType": "created",
                "notificationUrl": notification_url,
                "resource": self._subscription_resource(),
                "expirationDateTime": expiration.isoformat().replace("+00:00", "Z"),
                "clientState": client_state,
                "latestSupportedTlsVersion": "v1_2",
            },
        )
        return response

    def _subscription_resource(self) -> str:
        folder = self.config.source_folder
        if folder.replace(" ", "").casefold() == "inbox":
            return f"users/{self.config.mailbox}/mailFolders('Inbox')/messages"
        folder_id = self.resolve_folder_id(folder)
        return f"users/{self.config.mailbox}/mailFolders/{folder_id}/messages"

    def get_or_create_folder(self, display_name: str) -> str:
        folder_id = self._try_find_folder_id(display_name)
        if folder_id:
            return folder_id
        url = self._url(f"/users/{self._mailbox}/mailFolders")
        response = self._request("POST", url, json={"displayName": display_name})
        return response["id"]

    def resolve_folder_id(self, folder_name: str) -> str:
        well_known = {
            "inbox": "inbox",
            "sentitems": "sentitems",
            "drafts": "drafts",
            "deleteditems": "deleteditems",
            "archive": "archive",
        }
        key = folder_name.replace(" ", "").lower()
        if key in well_known:
            return well_known[key]
        folder_id = self._try_find_folder_id(folder_name)
        if not folder_id:
            raise ValueError(f"Mail folder not found: {folder_name}")
        return folder_id

    def _try_find_folder_id(self, display_name: str) -> str | None:
        url = self._url(f"/users/{self._mailbox}/mailFolders")
        response = self._request(
            "GET",
            url,
            params={
                "$top": "100",
                "$select": "id,displayName",
            },
        )
        for item in response.get("value", []):
            if item.get("displayName", "").casefold() == display_name.casefold():
                return item["id"]
        return None

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        response = self.session.request(method, url, headers=headers, timeout=60, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Graph request failed: {method} {url} -> "
                f"{response.status_code} {response.text[:500]}"
            )
        if not response.content:
            return {}
        return response.json()

    def _subject_matches(self, subject: str | None) -> bool:
        keywords = self.config.subject_keywords
        if not keywords:
            return True
        subject_value = (subject or "").casefold()
        return any(keyword.casefold() in subject_value for keyword in keywords)

    @property
    def _token(self) -> str:
        if self._access_token:
            return self._access_token
        token_url = (
            f"https://login.microsoftonline.com/{quote(self.config.tenant_id)}/"
            "oauth2/v2.0/token"
        )
        response = self.session.post(
            token_url,
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "client_credentials",
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=60,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                "Graph token request failed: "
                f"{response.status_code} {response.text[:500]}"
            )
        self._access_token = response.json()["access_token"]
        return self._access_token

    @property
    def _mailbox(self) -> str:
        return quote(self.config.mailbox)

    @staticmethod
    def _url(path: str) -> str:
        return GRAPH_ROOT + path
