from re import T
from django.db import models
from django.utils import timezone


class APIRequest(models.Model):
    title = models.CharField(max_length=200)
    endpoint = models.TextField(null=True, blank=True)
    ticker = models.TextField(null=True, blank=True)
    market = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    user_email = models.TextField(null=True, blank=True)
    user_country = models.TextField(null=True, blank=True)
    
    created = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created']
      