from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()

class Media(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        ICON = "icon", "Icon"

    file = models.FileField(upload_to="media/")
    type = models.CharField(max_length=10, choices=MediaType.choices)
    order = models.PositiveIntegerField(default=0)

    # Generic relation fields
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "order"]),
        ]


class Article(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
    )


    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    media = GenericRelation(
        Media,
        related_query_name="articles",
    )


class IconCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Icon(models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to="icons/")
    category = models.ForeignKey(
        IconCategory,
        related_name="icons",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)



class AuditLog(models.Model):

    ACTION_CHOICES = (
        ("created", "Created"),
        ("price_changed", "Price_Changed"),
        ("status_changed", "Status_Changed"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
        ("snapshot", "Snapshot"),

    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]