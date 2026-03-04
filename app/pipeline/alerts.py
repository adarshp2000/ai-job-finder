from plyer import notification

def notify(title: str, message: str):
    notification.notify(
        title=title[:64],
        message=message[:256],
        timeout=8
    )