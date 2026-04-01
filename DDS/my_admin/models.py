from django.db import models
from django.contrib.auth.models import User


# ==========================================
# SECTION 1: USER & ORGANIZATION DATA
# ==========================================

class InsuranceCompany(models.Model):
    name = models.CharField(max_length=100)
    company_code = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ('User', 'Standard User'),
        ('Agent', 'Insurance Agent'),
        ('Admin', 'System Administrator'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='User')
    company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ==========================================
# SECTION 2: REFERENCE & ANALYSIS DATA
# ==========================================

class VehicleValue(models.Model):
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.make} {self.model} ({self.year})"


class DamageAnalysis(models.Model):
    # Core Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_claims')
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_claims'
    )

    # Metadata
    car_details = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Pending')  # Pending, Approved, Rejected, Appealed
    damage_level = models.CharField(max_length=20, default='TBD')

    # Timestamps
    date_analyzed = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)  # Updates every time .save() is called

    # Valuation parameters adjusted by Agent
    market_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    minor_coeff = models.FloatField(null=True, blank=True, default=0.025)
    moderate_coeff = models.FloatField(null=True, blank=True, default=0.05)
    major_coeff = models.FloatField(null=True, blank=True, default=0.1)
    estimated_claim = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # --- DISPUTE RESOLUTION FIELDS ---
    agent_comment = models.TextField(null=True, blank=True)
    user_appeal_reason = models.TextField(null=True, blank=True)
    appeal_count = models.IntegerField(default=0)  # Tracks 1st and 2nd re-evaluation requests

    def __str__(self):
        return f"Analysis {self.id} - {self.car_details}"


# ==========================================
# SECTION 3: IMAGE & TECHNICAL STORES
# ==========================================

class ClaimImage(models.Model):
    """Store for all images uploaded for a specific analysis."""
    analysis = models.ForeignKey(DamageAnalysis, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='damage_scans/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Analysis #{self.analysis.id}"


class DamageReport(models.Model):
    """Detailed technical breakdown generated after AI processing."""
    analysis = models.OneToOneField(DamageAnalysis, on_delete=models.CASCADE)
    parts_affected = models.TextField(help_text="Comma-separated list of parts: Bumper, Hood, etc.")
    severity_scores = models.TextField(help_text="Confidence scores from AI for each part")
    ai_recommendation = models.TextField(default="Pending technical review")
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Analysis #{self.analysis.id}"


# ==========================================
# SECTION 4: FINANCIAL & COMPLAINT STORES
# ==========================================

class InsuranceClaim(models.Model):
    """The legal and financial database for final payouts."""
    CLAIM_STATUS = (
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Paid', 'Paid Out'),
        ('Rejected', 'Rejected'),
    )
    analysis = models.OneToOneField(DamageAnalysis, on_delete=models.CASCADE)
    policy_number = models.CharField(max_length=50, unique=True)
    final_settlement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    claim_status = models.CharField(max_length=20, choices=CLAIM_STATUS, default='Submitted')
    agent_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Claim {self.policy_number} - {self.claim_status}"


class UserComplaint(models.Model):
    """Escalated grievances for Admin review (3rd-tier dispute)."""
    PRIORITY = (('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    claim = models.ForeignKey(DamageAnalysis, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY, default='Medium')
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.user.username}: {self.subject}"