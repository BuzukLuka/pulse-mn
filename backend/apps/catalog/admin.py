from django.contrib import admin
from .models import Category, District, Province

admin.site.register([Category, District, Province])
