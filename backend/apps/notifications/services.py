from .models import Notification


def notify(user, title, body="", content_id=None):
    return Notification.objects.create(user=user, title=title, body=body, content_id=content_id)


def notify_editors(title, body="", content_id=None):
    """Редакторын дараалалд шинэ контент орсныг мэдэгдэнэ (FR-025)."""
    from apps.accounts.models import Role, User
    Notification.objects.bulk_create([
        Notification(user=u, title=title, body=body, content_id=content_id)
        for u in User.objects.filter(role=Role.EDITOR, is_active=True)
    ])
