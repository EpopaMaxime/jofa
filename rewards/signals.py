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
            if old_order.status != 'completed' and instance.status == 'completed':
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
