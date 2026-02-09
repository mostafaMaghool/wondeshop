from django.db import models
from django.contrib.auth.models import AbstractUser

#Mostafa
class User(AbstractUser):

    class AdminRole(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        SITE_ADMIN = "site_admin", "Site Admin"

    admin_role = models.CharField(
        max_length=20,
        choices=AdminRole.choices,
        null=True,
        blank=True,
    )


    phone = models.CharField(max_length=20, blank=True, null=True)
    class Meta:
        verbose_name = 'user'
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)