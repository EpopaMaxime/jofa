from django.db.models.signals import pre_save
from django.dispatch import receiver
from orders.models import Order
from rewards.models import RewardPoint
from rewards.utils import award_points

@receiver(pre_save, sender=Order)
def pre_save_order_points(sender, instance, **kwargs):
    # Only act if the instance is already in the database
    if instance.id:
        try:
            old_order = Order.objects.get(id=instance.id)
            # Award points only if the order was not paid before and is now marked as paid
            # AND the order belongs to a registered user
            if not old_order.paid and instance.paid and instance.user:
                # Check if points have already been awarded for this order
                already_awarded = RewardPoint.objects.filter(
                    user=instance.user,
                    transaction_type='earned',
                    order_reference=str(instance.id)
                ).exists()

                if not already_awarded:
                    award_points(instance.user, instance)
        except Order.DoesNotExist:
            pass
