"""プラットフォーム固有ユーティリティ（Windows）"""
import os
import subprocess
import tempfile
import webbrowser


def copy_to_clipboard(text):
    """テキストをクリップボードにコピーする（Windows）"""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    )
    try:
        tmp.write(text)
        tmp.close()
        subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                f"Get-Content -Path '{tmp.name}' -Encoding UTF8 -Raw "
                f"| Set-Clipboard"
            ],
            creationflags=0x08000000,
            check=True,
        )
    finally:
        os.unlink(tmp.name)


def notify_windows(title, message):
    """Windows トースト通知を送信する"""
    try:
        ps_cmd = (
            f"[Windows.UI.Notifications.ToastNotificationManager, "
            f"Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
            f"$template = [Windows.UI.Notifications.ToastNotificationManager]"
            f"::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]"
            f"::ToastText02); "
            f"$text = $template.GetElementsByTagName('text'); "
            f"$text.Item(0).AppendChild($template.CreateTextNode('{title}')); "
            f"$text.Item(1).AppendChild($template.CreateTextNode('{message}')); "
            f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
            f"[Windows.UI.Notifications.ToastNotificationManager]"
            f"::CreateToastNotifier('ETH Terminal').Show($toast)"
        )
        subprocess.Popen(
            ["powershell", "-Command", ps_cmd],
            creationflags=0x08000000
        )
    except Exception:
        print(f"  [通知] {title}: {message}")


def open_url(url):
    """URLをデフォルトブラウザで開く"""
    webbrowser.open(url)
