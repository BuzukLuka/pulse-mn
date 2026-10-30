from django.contrib import admin
from .models import DataSource, Indicator, IndicatorValue, IndicatorValueHistory

admin.site.register([DataSource, Indicator, IndicatorValue, IndicatorValueHistory])
