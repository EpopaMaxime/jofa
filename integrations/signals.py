"""When a COD shipment is marked delivered, collect payment."""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Shipment


@receiver(pre_save, sender=Shipment)
def collect_cod_on_delivery(sender, instance: Shipment, **kwargs):
    if instance.status != 'delivered':
        return
    if not instance.pk:
        return

    try:
        previous = Shipment.objects.get(pk=instance.pk)
    except Shipment.DoesNotExist:
        return

    if previous.status == 'delivered':
        return

    order = instance.order
    if order.paid:
        return

    cod_txn = (
        order.payments.filter(provider_slug='cod')
        .exclude(status__in=['cancelled', 'failed', 'refunded'])
        .order_by('-created_at')
        .first()
    )
    if not cod_txn:
        return

    cod_txn.mark_succeeded(
        external_id=cod_txn.external_id or f'cod_delivered_{order.id}',
        raw={
            **(cod_txn.raw_response or {}),
            'collected_on_delivery': True,
            'shipment_id': instance.pk,
        },
    )
