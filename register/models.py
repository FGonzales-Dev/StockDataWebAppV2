from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.crypto import get_random_string

from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    user_key = models.CharField(max_length=16)
 
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance, user_key=get_random_string(10, 'abcdef0123456789'))

# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()

# post_save.connect(create_profile, sender=User)
# post_save.connect(save_profile, sender=User)


