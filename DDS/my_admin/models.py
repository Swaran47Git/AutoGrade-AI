from django.db import models
from django.contrib.auth.models import User


# 1. THE PEOPLE
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('User', 'User'), ('Agent', 'Agent'), ('Admin', 'Admin')],
                            default='User')


# 2. THE PRICE LIST
class VehicleValue(models.Model):
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)


# 3. THE MASTER CLAIM (Combined Analysis + Financials)
class DamageAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')

    damage_level = models.CharField(max_length=20, default='TBD')
    total_damage_factor = models.FloatField(default=0.0)
    detected_parts = models.CharField(max_length=255, null=True, blank=True)

    car_details = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Pending')  # Pending, Approved, Appealed, Escalated

    market_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_claim = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Coefficients (Stored here so agent can override per-claim)
    minor_coeff = models.FloatField(default=0.025)
    moderate_coeff = models.FloatField(default=0.05)
    major_coeff = models.FloatField(default=0.1)

    # Dispute Logic
    agent_comment = models.TextField(null=True, blank=True)
    user_appeal_reason = models.TextField(null=True, blank=True)
    appeal_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# 4. THE PHOTOS
class ClaimImage(models.Model):
    analysis = models.ForeignKey(DamageAnalysis, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='damage_scans/')

class UserComplaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    claim = models.ForeignKey(DamageAnalysis, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# 5. THE AI LEDGER (This replaces the messy JSONField)
class DamageDetection(models.Model):
    analysis = models.ForeignKey(DamageAnalysis, on_delete=models.CASCADE, related_name='detections')
    severity = models.CharField(max_length=20)  # major, moderate, minor
    box_coords = models.CharField(max_length=100)  # [x,y,w,h]
    source_image = models.ForeignKey(ClaimImage, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=True)  # Agent can "uncheck" this