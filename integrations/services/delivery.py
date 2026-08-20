"""Delivery / logistics adapters."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from integrations.models import IntegrationProvider, Shipment


class BaseDeliveryProvider:
    slug = 'base'

    def create_shipment(self, order) -> Shipment:
        raise NotImplementedError


class ManualDeliveryProvider(BaseDeliveryProvider):
    slug = 'manual'

    def create_shipment(self, order) -> Shipment:
        provider = IntegrationProvider.objects.filter(
            slug=self.slug, category='delivery'
        ).first()
        return Shipment.objects.create(
            order=order,
            provider=provider,
            provider_slug=self.slug,
            tracking_number=f'JOFA-{order.id}-{uuid.uuid4().hex[:6].upper()}',
            status='pending',
            carrier_label='JOFA Local Dispatch',
            estimated_delivery=(timezone.now() + timedelta(days=3)).date(),
            metadata={'city': order.city, 'address': order.address},
        )


class MockCourierProvider(BaseDeliveryProvider):
    """Placeholder for future vendor APIs (GIG, DHL, etc.)."""

    slug = 'mock_courier'

    def create_shipment(self, order) -> Shipment:
        provider = IntegrationProvider.objects.filter(
            slug=self.slug, category='delivery'
        ).first()
        return Shipment.objects.create(
            order=order,
            provider=provider,
            provider_slug=self.slug,
            tracking_number=f'MCK{uuid.uuid4().hex[:10].upper()}',
            status='ready',
            carrier_label=getattr(settings, 'DELIVERY_CARRIER_NAME', 'Partner Courier'),
            estimated_delivery=(timezone.now() + timedelta(days=2)).date(),
            metadata={'api': 'mock', 'city': order.city},
        )


def get_delivery_provider(slug: str | None = None) -> BaseDeliveryProvider:
    preferred = slug or getattr(settings, 'DELIVERY_PROVIDER', 'manual')
    registry = {
        'manual': ManualDeliveryProvider,
        'mock_courier': MockCourierProvider,
    }
    return registry.get(preferred, ManualDeliveryProvider)()


def create_shipment_for_order(order) -> Shipment:
    if order.shipments.exists():
        return order.shipments.first()
    return get_delivery_provider().create_shipment(order)
