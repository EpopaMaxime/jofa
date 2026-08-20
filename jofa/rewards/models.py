from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class RewardSetting(models.Model):
    """
    Singleton model to hold rewards configuration criteria.
    Only one instance of this model is allowed.
    """
    points_per_amount = models.IntegerField(default=1, help_text="Number of points earned per specific amount spent.")
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00, help_text="Amount to be spent to earn the points.")
    bonus_points = models.IntegerField(default=50, help_text="Bonus points for frequent transactions.")
    bonus_threshold = models.IntegerField(default=5, help_text="Number of transactions within 30 days to trigger bonus points.")
    points_to_cash_ratio = models.DecimalField(max_digits=8, decimal_places=2, default=0.50, help_text="Cash value per point (e.g., 1000 points = 500 FCFA -> ratio = 0.50).")
    expiry_days = models.IntegerField(default=365, help_text="Days until earned points expire.")

    def save(self, *args, **kwargs):
        if not self.pk and RewardSetting.objects.exists():
            raise ValidationError('There can be only one RewardSetting instance')
        return super(RewardSetting, self).save(*args, **kwargs)

    def clean(self):
        if not self.pk and RewardSetting.objects.exists():
            raise ValidationError('There is already a RewardSetting instance.')

    def __str__(self):
        return "Reward System Settings"

    class Meta:
        verbose_name = "Reward Setting"
        verbose_name_plural = "Reward Settings"

class RewardPoint(models.Model):
    """
    Model to track points earning, redemption, and expiration for each user.
    """
    TRANSACTION_TYPES = [
        ('earned', 'Earned'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_points')
    points = models.IntegerField(help_text="Positive for earned, negative for redeemed/expired.")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    order_reference = models.CharField(max_length=100, blank=True, help_text="Order ID or reference code.")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.transaction_type})"

    class Meta:
        ordering = ['-created_at']

class LoyaltyTier(models.Model):
    """
    Model to define different levels of loyalty.
    """
    name = models.CharField(max_length=50, unique=True)
    min_points = models.IntegerField(help_text="Minimum total points required to reach this tier.")
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=20, default="#A58B7C", help_text="Hex color for the tier (e.g., #A58B7C).")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Min: {self.min_points} pts)"

    class Meta:
        ordering = ['min_points']

class TierBenefit(models.Model):
    """
    Specific benefits associated with a loyalty tier.
    """
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.CASCADE, related_name='benefits')
    benefit = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.tier.name} - {self.benefit}"

class EarnMethod(models.Model):
    """
    Describes ways users can earn points.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_awarded = models.CharField(max_length=100, help_text="Text description of points (e.g., '50 points' or '1 pt / 1000 FCFA').")
    icon_svg = models.TextField(blank=True, help_text="Optional SVG path for the icon.")
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']
