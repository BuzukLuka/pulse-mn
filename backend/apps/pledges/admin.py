from django.contrib import admin
from .models import Pledge, PledgeEvidence, PledgeStatusHistory, Politician

admin.site.register([Politician, Pledge, PledgeEvidence, PledgeStatusHistory])
