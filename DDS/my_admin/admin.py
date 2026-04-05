from django.contrib import admin
from .models import UserProfile, VehicleValue, DamageAnalysis, ClaimImage, DamageDetection

# Register the models so they appear in the /admin/ panel
admin.site.register(UserProfile)
admin.site.register(VehicleValue)

# Optional: Make the DamageAnalysis view more detailed in Admin
class DamageAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'car_details', 'user', 'status', 'estimated_claim', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('car_details', 'user__username')

admin.site.register(DamageAnalysis, DamageAnalysisAdmin)

# Register these as well
admin.site.register(ClaimImage)
admin.site.register(DamageDetection)