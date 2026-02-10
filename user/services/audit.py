from django.contrib.contenttypes.models import ContentType

from user.api.admin_models import AuditLog


def log_snapshot_change(*, user, obj, before, after, action):
    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.id,
        before=obj,
        after=obj,
    )
