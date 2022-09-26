from django.contrib import admin
from .models import APIRequest
from register.models import Profile
from django.conf.locale.es import formats as es_formats



class APIRequestAdmin(admin.ModelAdmin):
    def time_seconds(self, obj):
        return obj.created.strftime("%b %d, %y, %I:%M:%S %p")
    list_display = ('title','ticker', 'time_seconds','user_email', 'user_country')



admin.site.register(APIRequest,APIRequestAdmin)