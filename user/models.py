from django.db import models
from django.contrib.auth.models import AbstractUser

#Mostafa
class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)

    class AdminRole(models.TextChoices):
            SUPER_ADMIN = "SUPER_ADMIN", "Super Administrator"
            SITE_ADMIN  = "SITE_ADMIN",  "Site Administrator"

    admin_role = models.CharField(
        max_length=20,
        choices=AdminRole.choices,
        default=None,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'user'
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)