from decimal import Decimal
from django.utils import timezone
from .models import RewardSetting, RewardPoint
from orders.models import Order
from datetime import timedelta

def award_points(user, order):
    """
    Calculate and award points for the given order, based on the RewardSetting.
    Applies any bonus points if the user has reached the threshold within 30 days.
    """
    setting = RewardSetting.objects.first()
    if not setting:
        return 0
    
    # Calculate base points based on the order total
    total = order.get_total_cost()
    points_earned = int((total / setting.amount_spent) * setting.points_per_amount)
    
    if points_earned > 0:
        # Check for bonus points
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders_count = Order.objects.filter(
            user=user, 
            created__gte=thirty_days_ago
        ).count()

        if recent_orders_count >= setting.bonus_threshold:
            points_earned += setting.bonus_points

        # Calculate expiry date
        expiry_date = timezone.now() + timedelta(days=setting.expiry_days)

        # Create the point record
        RewardPoint.objects.create(
            user=user,
            points=points_earned,
            transaction_type='earned',
            order_reference=str(order.id),
            expires_at=expiry_date
        )
    return points_earned

def get_user_points(user):
    """
    Returns the user's available (valid) points.
    Filters out expired points dynamically.
    """
    now = timezone.now()
    # It takes the sum of all 'earned' minus 'redeemed' and 'expired'.
    # Because we store redeemed as negative numbers, and earned as positive.
    # We only sum 'earned' points that haven't expired, and all 'redeemed'.
    # Actually wait. If a point is earned and it expires, you lose it.
    # To keep things simple, we can just aggregate points that haven't expired minus all redeemed.
    
    from django.db.models import Sum
    # Sum of earned points that are still valid
    earned = RewardPoint.objects.filter(
        user=user, 
        transaction_type='earned',
        expires_at__gt=now
    ).aggregate(Sum('points'))['points__sum'] or 0
    
    # Redeemed points are stored as negative numbers
    redeemed = RewardPoint.objects.filter(
        user=user, 
        transaction_type='redeemed'
    ).aggregate(Sum('points'))['points__sum'] or 0

    return max(0, earned + redeemed)
