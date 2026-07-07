from .models import Notification


def notification_counts(request):
    data = {
        'unread_notifications_count': 0,
        'unread_admin_notifications_count': 0,
    }
    if request.user.is_authenticated:
        if request.user.is_staff:
            data['unread_admin_notifications_count'] = Notification.objects.filter(
                user__isnull=True, is_read=False
            ).count()
        data['unread_notifications_count'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    return data
