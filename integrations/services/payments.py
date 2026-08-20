"""Payment gateway adapters — multi-vendor registry (COD, Stripe, simulate, …)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.urls import reverse

from integrations.models import IntegrationProvider, PaymentTransaction


class PaymentError(Exception):
    pass


class BasePaymentGateway:
    slug = 'base'
    label = 'Payment'
    description = ''

    def create_payment(self, order, request) -> PaymentTransaction:
        raise NotImplementedError

    def finalize(self, transaction: PaymentTransaction, request) -> PaymentTransaction:
        raise NotImplementedError

    def is_available(self) -> bool:
        return True


class CashOnDeliveryGateway(BasePaymentGateway):
    """Pay in cash when the order is delivered."""

    slug = 'cod'
    label = 'Cash on delivery'
    description = 'Pay the courier in cash when your order arrives. No online charge now.'

    def create_payment(self, order, request) -> PaymentTransaction:
        provider = IntegrationProvider.objects.filter(
            slug=self.slug, category='payment'
        ).first()
        amount = Decimal(order.get_total_cost())
        return PaymentTransaction.objects.create(
            order=order,
            provider=provider,
            provider_slug=self.slug,
            amount=amount,
            currency=getattr(settings, 'PAYMENT_CURRENCY', 'XAF'),
            status='pending',
            external_id=f'cod_{uuid.uuid4().hex[:16]}',
            raw_response={'mode': 'cod', 'collect_on_delivery': True},
        )

    def finalize(self, transaction: PaymentTransaction, request) -> PaymentTransaction:
        """Confirm the COD order (not paid yet — collected on delivery)."""
        transaction.status = 'pending'
        transaction.raw_response = {
            **(transaction.raw_response or {}),
            'cod_confirmed': True,
            'confirmed_by': getattr(request.user, 'username', 'guest'),
        }
        transaction.save(update_fields=['status', 'raw_response', 'updated_at'])

        order = transaction.order
        order.paid = False
        if order.status == 'cancelled':
            order.status = 'pending'
        order.save(update_fields=['paid', 'status', 'updated'])
        return transaction


class SimulatePaymentGateway(BasePaymentGateway):
    """Local/dev card simulation — succeeds when user confirms."""

    slug = 'simulate'
    label = 'Card (test)'
    description = 'Development simulation — no real charge.'

    def create_payment(self, order, request) -> PaymentTransaction:
        provider = IntegrationProvider.objects.filter(
            slug=self.slug, category='payment'
        ).first()
        amount = Decimal(order.get_total_cost())
        return PaymentTransaction.objects.create(
            order=order,
            provider=provider,
            provider_slug=self.slug,
            amount=amount,
            currency=getattr(settings, 'PAYMENT_CURRENCY', 'XAF'),
            status='requires_action',
            external_id=f'sim_{uuid.uuid4().hex[:16]}',
            raw_response={'mode': 'simulate'},
        )

    def finalize(self, transaction: PaymentTransaction, request) -> PaymentTransaction:
        transaction.mark_succeeded(
            external_id=transaction.external_id or f'sim_{uuid.uuid4().hex[:12]}',
            raw={'confirmed_by': getattr(request.user, 'username', 'guest')},
        )
        return transaction


class StripePaymentGateway(BasePaymentGateway):
    slug = 'stripe'
    label = 'Card (Stripe)'
    description = 'Pay securely online with Stripe.'

    def is_available(self) -> bool:
        return bool(getattr(settings, 'STRIPE_SECRET_KEY', ''))

    def create_payment(self, order, request) -> PaymentTransaction:
        secret = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not secret:
            raise PaymentError('Stripe is not configured (STRIPE_SECRET_KEY missing).')

        import stripe

        stripe.api_key = secret
        provider = IntegrationProvider.objects.filter(
            slug=self.slug, category='payment'
        ).first()
        amount = Decimal(order.get_total_cost())
        unit_amount = int(amount)

        success_url = (
            request.build_absolute_uri(reverse('integrations:payment_success'))
            + '?session_id={CHECKOUT_SESSION_ID}'
        )
        cancel_url = request.build_absolute_uri(
            reverse('integrations:payment_cancel', args=[order.id])
        )

        session = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=order.email,
            line_items=[
                {
                    'price_data': {
                        'currency': getattr(settings, 'STRIPE_CURRENCY', 'xaf'),
                        'product_data': {'name': f'JOFA Order #{order.id}'},
                        'unit_amount': unit_amount,
                    },
                    'quantity': 1,
                }
            ],
            metadata={'order_id': str(order.id)},
        )

        return PaymentTransaction.objects.create(
            order=order,
            provider=provider,
            provider_slug=self.slug,
            amount=amount,
            currency=getattr(settings, 'PAYMENT_CURRENCY', 'XAF'),
            status='requires_action',
            external_id=session.id,
            raw_response={'checkout_url': session.url, 'session_id': session.id},
        )

    def finalize(self, transaction: PaymentTransaction, request) -> PaymentTransaction:
        secret = getattr(settings, 'STRIPE_SECRET_KEY', '')
        import stripe

        stripe.api_key = secret
        session = stripe.checkout.Session.retrieve(transaction.external_id)
        if session.payment_status == 'paid':
            transaction.mark_succeeded(
                external_id=session.id,
                raw={'payment_status': session.payment_status},
            )
        else:
            transaction.status = 'failed'
            transaction.raw_response = {'payment_status': session.payment_status}
            transaction.save()
        return transaction


GATEWAY_REGISTRY = {
    'cod': CashOnDeliveryGateway,
    'simulate': SimulatePaymentGateway,
    'stripe': StripePaymentGateway,
}


def get_payment_gateway(slug: str | None = None) -> BasePaymentGateway:
    preferred = slug or getattr(settings, 'PAYMENT_PROVIDER', 'cod')
    if preferred == 'stripe' and not getattr(settings, 'STRIPE_SECRET_KEY', ''):
        preferred = 'cod'
    cls = GATEWAY_REGISTRY.get(preferred, CashOnDeliveryGateway)
    return cls()


def list_available_payment_methods() -> list[dict]:
    """
    Multi-vendor payment methods available at checkout.
    Prefer active IntegrationProvider rows; always expose configured gateways.
    """
    db_providers = {}
    try:
        db_providers = {
            p.slug: p
            for p in IntegrationProvider.objects.filter(
                category='payment', is_active=True
            )
        }
    except Exception:
        db_providers = {}

    methods = []
    for slug in ('cod', 'stripe', 'simulate'):
        cls = GATEWAY_REGISTRY.get(slug)
        if not cls:
            continue
        gateway = cls()
        if not gateway.is_available():
            continue
        if slug == 'simulate' and not getattr(settings, 'DEBUG', False):
            if slug not in db_providers:
                continue
        # If DB has providers, only show those marked active (except always keep COD)
        if db_providers and slug not in db_providers and slug != 'cod':
            continue
        provider = db_providers.get(slug)
        methods.append(
            {
                'slug': slug,
                'label': (provider.name if provider else gateway.label),
                'description': gateway.description,
                'is_default': bool(
                    provider.is_default
                    if provider
                    else slug == getattr(settings, 'PAYMENT_PROVIDER', 'cod')
                ),
            }
        )

    if not methods:
        methods.append(
            {
                'slug': 'cod',
                'label': 'Cash on delivery',
                'description': CashOnDeliveryGateway.description,
                'is_default': True,
            }
        )

    if not any(m['is_default'] for m in methods):
        # Prefer COD as default
        for m in methods:
            if m['slug'] == 'cod':
                m['is_default'] = True
                break
        else:
            methods[0]['is_default'] = True
    return methods
