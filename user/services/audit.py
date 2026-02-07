from user.api.admin_models import AuditLog


def log_action(*, user, action, obj, metadata=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=obj.pk,
        metadata=metadata or {},
    )
