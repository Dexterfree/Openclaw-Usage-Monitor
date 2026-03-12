"""
Notification utilities for OpenCLAW Token Usage Monitor.

This module provides desktop notification functionality.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_notification(
    title: str,
    message: str,
    icon: Optional[str] = None,
) -> bool:
    """
    Send a desktop notification.

    Args:
        title: Notification title
        message: Notification message
        icon: Optional path to icon file

    Returns:
        True if notification was sent successfully
    """
    try:
        # Try plyer first (cross-platform)
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="OpenCLAW Monitor",
            app_icon=icon,
        )
        return True
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Plyer notification failed: {e}")

    # Try platform-specific methods
    import platform
    system = platform.system()

    if system == "Darwin":  # macOS
        return _send_macos_notification(title, message)
    elif system == "Linux":
        return _send_linux_notification(title, message)
    elif system == "Windows":
        return _send_windows_notification(title, message)

    return False


def _send_macos_notification(title: str, message: str) -> bool:
    """Send notification on macOS using osascript."""
    try:
        import subprocess

        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=True)
        return True
    except Exception as e:
        logger.debug(f"macOS notification failed: {e}")
        return False


def _send_linux_notification(title: str, message: str) -> bool:
    """Send notification on Linux using notify-send."""
    try:
        import subprocess

        subprocess.run(
            ["notify-send", title, message],
            check=True,
        )
        return True
    except FileNotFoundError:
        logger.debug("notify-send not found")
        return False
    except Exception as e:
        logger.debug(f"Linux notification failed: {e}")
        return False


def _send_windows_notification(title: str, message: str) -> bool:
    """Send notification on Windows using toast."""
    try:
        from win10toast import ToastNotifier

        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5)
        return True
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Windows notification failed: {e}")

    # Fallback: try using PowerShell
    try:
        import subprocess

        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $template = @"
        <toast>
            <visual>
                <binding template="ToastGeneric">
                    <text>{title}</text>
                    <text>{message}</text>
                </binding>
            </visual>
        </toast>
        "@
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("OpenCLAW Monitor")
        $notifier.Show($toast)
        '''
        subprocess.run(
            ["powershell", "-Command", ps_script],
            check=True,
        )
        return True
    except Exception as e:
        logger.debug(f"Windows PowerShell notification failed: {e}")

    return False


def can_send_notifications() -> bool:
    """
    Check if desktop notifications are available.

    Returns:
        True if notifications can be sent
    """
    try:
        from plyer import notification
        return True
    except ImportError:
        pass

    import platform
    system = platform.system()

    if system == "Linux":
        import shutil
        return shutil.which("notify-send") is not None

    return system in ["Darwin", "Windows"]
