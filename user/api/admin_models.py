from django.db.models import TextField, Model, FileField
from django.forms import SlugField, CharField, DateTimeField


class Article(Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
    )

    title = CharField(max_length=200)
    slug = SlugField(unique=True)
    content = TextField()
    status = CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = DateTimeField(auto_now_add=True)

class Media(Model):
    MEDIA_TYPE = (
        ("image", "Image"),
        ("video", "Video"),
        ("icon", "Icon"),
    )

    file = FileField(upload_to="media/")
    type = CharField(max_length=10, choices=MEDIA_TYPE)
    created_at = DateTimeField(auto_now_add=True)

class Icon(models.Model):
    name = models.CharField(max_length=50)
    svg = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
