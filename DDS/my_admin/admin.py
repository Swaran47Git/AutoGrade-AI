from django.contrib import admin

# Register your models here.
from .models import ClaimImage, DamageReport, InsuranceClaim, UserComplaint
# Add these lines to admin.py
admin.site.register(ClaimImage)
admin.site.register(DamageReport)
admin.site.register(InsuranceClaim)
admin.site.register(UserComplaint)