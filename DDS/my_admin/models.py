from django.db import models
from django.contrib.auth.models import User

# TABLE 1: Your Reference Data (The 5 Cars)
class VehicleValue(models.Model):
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    market_value = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.make} {self.model} ({self.year})"

# TABLE 2: The AI Analysis Results
class DamageAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_info = models.CharField(max_length=100)
    market_value = models.PositiveIntegerField()
    damage_level = models.CharField(max_length=20)
    damage_coefficient = models.FloatField()
    estimated_claim_amount = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.vehicle_info} ({self.damage_level})"