from django.contrib import admin
from .models import Content, Media

admin.site.register([Content, Media])
