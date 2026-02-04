"""Notification system for sending alerts through various channels."""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console

from .config import NotificationSettings
from .models import Alert


class NotificationChannel(ABC):
    """Base class for notification channels."""

    name: str = "base"

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send an alert through this channel.

        Args:
            alert: The alert to send

        Returns:
            True if sent successfully
        """
        raise NotImplementedError

    @abstractmethod
    async def send_batch(self, alerts: list[Alert]) -> int:
        """Send multiple alerts through this channel.

        Args:
            alerts: List of alerts to send

        Returns:
            Number of alerts sent successfully
        """
        raise NotImplementedError


class ConsoleNotificationChannel(NotificationChannel):
    """Send alerts to the console using rich formatting."""

    name = "console"

    def __init__(self):
        self.console = Console()

    async def send(self, alert: Alert) -> bool:
        """Print alert to console."""
        try:
            self.console.print(alert.format_console())
            return True
        except Exception as e:
            self.console.print(f"[red]Error displaying alert: {e}[/red]")
            return False

    async def send_batch(self, alerts: list[Alert]) -> int:
        """Print all alerts to console."""
        success_count = 0
        for alert in alerts:
            if await self.send(alert):
                success_count += 1
        return success_count


class SlackNotificationChannel(NotificationChannel):
    """Send alerts to Slack via webhook."""

    name = "slack"

    def __init__(self, webhook_url: str, channel: str = "#insider-alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
        self._client: Optional["httpx.AsyncClient"] = None

    async def _get_client(self) -> "httpx.AsyncClient":
        """Get or create HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def send(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        if not self.webhook_url:
            return False

        try:
            client = await self._get_client()

            payload = alert.format_slack()
            payload["channel"] = self.channel

            response = await client.post(
                self.webhook_url,
                json=payload,
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False

    async def send_batch(self, alerts: list[Alert]) -> int:
        """Send multiple alerts to Slack with rate limiting."""
        success_count = 0

        for alert in alerts:
            if await self.send(alert):
                success_count += 1
            # Rate limit to avoid Slack API limits
            await asyncio.sleep(1)

        return success_count

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class EmailNotificationChannel(NotificationChannel):
    """Send alerts via email."""

    name = "email"

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_addr: str,
        to_addrs: list[str],
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self.to_addrs = to_addrs

    def _format_email_body(self, alert: Alert) -> str:
        """Format alert as email body."""
        lines = [
            f"Alert Type: {alert.alert_type.value}",
            f"Severity: {alert.severity.value.upper()}",
            f"Company: {alert.company.name} ({alert.company.ticker})",
            f"Time: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Summary:",
            alert.summary,
            "",
            "Transactions:",
        ]

        for tx in alert.transactions[:10]:
            direction = "BUY" if tx.transaction_type.value == "buy" else "SELL"
            lines.append(
                f"  - {tx.insider.name}: {direction} {tx.shares:,} shares "
                f"@ {tx.price_per_share_nok:.2f} NOK = {tx.total_value_nok:,.0f} NOK"
            )

        if alert.transactions and alert.transactions[0].source_url:
            lines.extend(["", f"Source: {alert.transactions[0].source_url}"])

        return "\n".join(lines)

    async def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        if not self.smtp_host or not self.to_addrs:
            return False

        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, "plain"))

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            return True

        except ImportError:
            print("aiosmtplib not installed. Run: pip install aiosmtplib")
            return False
        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False

    async def send_batch(self, alerts: list[Alert]) -> int:
        """Send multiple alerts via email."""
        success_count = 0

        for alert in alerts:
            if await self.send(alert):
                success_count += 1
            # Small delay between emails
            await asyncio.sleep(0.5)

        return success_count


class NotificationManager:
    """Manages multiple notification channels."""

    def __init__(self, settings: Optional[NotificationSettings] = None):
        self.settings = settings or NotificationSettings()
        self.channels: list[NotificationChannel] = []
        self._setup_channels()

    def _setup_channels(self) -> None:
        """Set up notification channels based on settings."""
        for channel_name in self.settings.channels:
            if channel_name == "console":
                self.channels.append(ConsoleNotificationChannel())

            elif channel_name == "slack":
                if self.settings.slack_webhook_url:
                    self.channels.append(
                        SlackNotificationChannel(
                            webhook_url=self.settings.slack_webhook_url,
                            channel=self.settings.slack_channel,
                        )
                    )

            elif channel_name == "email":
                if self.settings.email_smtp_host and self.settings.email_to:
                    self.channels.append(
                        EmailNotificationChannel(
                            smtp_host=self.settings.email_smtp_host,
                            smtp_port=self.settings.email_smtp_port,
                            smtp_user=self.settings.email_smtp_user,
                            smtp_password=self.settings.email_smtp_password,
                            from_addr=self.settings.email_from,
                            to_addrs=self.settings.email_to,
                        )
                    )

    def add_channel(self, channel: NotificationChannel) -> None:
        """Add a notification channel.

        Args:
            channel: The channel to add
        """
        self.channels.append(channel)

    async def send_alert(self, alert: Alert) -> dict[str, bool]:
        """Send an alert through all configured channels.

        Args:
            alert: The alert to send

        Returns:
            Dictionary mapping channel name to success status
        """
        results = {}

        for channel in self.channels:
            try:
                success = await channel.send(alert)
                results[channel.name] = success
            except Exception as e:
                print(f"Error sending to {channel.name}: {e}")
                results[channel.name] = False

        return results

    async def send_alerts(self, alerts: list[Alert]) -> dict[str, int]:
        """Send multiple alerts through all channels.

        Args:
            alerts: List of alerts to send

        Returns:
            Dictionary mapping channel name to count of successful sends
        """
        results = {}

        for channel in self.channels:
            try:
                count = await channel.send_batch(alerts)
                results[channel.name] = count
            except Exception as e:
                print(f"Error sending batch to {channel.name}: {e}")
                results[channel.name] = 0

        return results

    async def close(self) -> None:
        """Close all channels that require cleanup."""
        for channel in self.channels:
            if hasattr(channel, "close"):
                await channel.close()
