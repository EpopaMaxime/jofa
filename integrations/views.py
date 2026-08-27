from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from orders.access import get_accessible_order, user_can_access_order

from .models import PaymentTransaction
from .services.delivery import create_shipment_for_order
from .services.payments import (
    PaymentError,
    get_payment_gateway,
    list_available_payment_methods,
)


class PaymentCheckoutView(View):
    template_name = 'integrations/payment_checkout.html'

    def get(self, request, order_id):
        order = get_accessible_order(request, order_id)
        if order is None:
            messages.error(request, 'You can complete this order as a guest from the same browser, or sign in if you placed it with an account.')
            return redirect('accounts:login')
        if order.paid:
            messages.info(request, 'This order is already paid.')
            return redirect('orders:order_detail', order_id=order.id)

        methods = list_available_payment_methods()
        pending = (
            order.payments.filter(status__in=['pending', 'requires_action'])
            .order_by('-created_at')
            .first()
        )
        return render(
            request,
            self.template_name,
            {
                'order': order,
                'transaction': pending,
                'methods': methods,
                'amount': order.get_total_cost(),
            },
        )

    def post(self, request, order_id):
        order = get_accessible_order(request, order_id)
        if order is None:
            messages.error(request, 'You can complete this order as a guest from the same browser, or sign in if you placed it with an account.')
            return redirect('accounts:login')
        if order.paid:
            return redirect('orders:order_detail', order_id=order.id)

        method = request.POST.get('payment_method', '').strip()
        available = {m['slug'] for m in list_available_payment_methods()}
        if method not in available:
            messages.error(request, 'Please choose a valid payment method.')
            return redirect('integrations:payment_checkout', order_id=order.id)

        # Cancel previous unfinished attempts for a clean switch of vendor
        order.payments.filter(status__in=['pending', 'requires_action']).exclude(
            provider_slug=method
        ).update(status='cancelled')

        gateway = get_payment_gateway(method)
        try:
            txn = (
                order.payments.filter(
                    provider_slug=method, status__in=['pending', 'requires_action']
                )
                .order_by('-created_at')
                .first()
            )
            if not txn:
                txn = gateway.create_payment(order, request)
        except PaymentError as exc:
            messages.error(request, str(exc))
            return redirect('integrations:payment_checkout', order_id=order.id)

        checkout_url = (txn.raw_response or {}).get('checkout_url')
        if checkout_url and txn.provider_slug == 'stripe':
            return redirect(checkout_url)

        # COD + simulate: finalize immediately from this step
        gateway.finalize(txn, request)
        create_shipment_for_order(order)

        try:
            from core.utils import send_order_confirmation

            send_order_confirmation(order, request)
        except Exception:
            pass

        if method == 'cod':
            messages.success(
                request,
                'Order confirmed. Pay the courier in cash on delivery.',
            )
        else:
            messages.success(request, 'Payment successful. Your order is confirmed.')
        return redirect('orders:order_detail', order_id=order.id)


class PaymentConfirmView(View):
    """Confirm a pending simulate/COD transaction (legacy endpoint)."""

    def post(self, request, order_id):
        if get_accessible_order(request, order_id) is None:
            messages.error(request, 'Access denied.')
            return redirect('accounts:login')
        method = request.POST.get('payment_method') or 'cod'
        request.POST = request.POST.copy()
        request.POST['payment_method'] = method
        view = PaymentCheckoutView()
        view.request = request
        view.args = ()
        view.kwargs = {'order_id': order_id}
        return view.post(request, order_id)


class PaymentSuccessView(View):
    def get(self, request):
        session_id = request.GET.get('session_id')
        if not session_id:
            return HttpResponseBadRequest('Missing session_id')
        txn = get_object_or_404(PaymentTransaction, external_id=session_id)
        if not user_can_access_order(request, txn.order):
            messages.error(request, 'Access denied.')
            return redirect('core:home')
        gateway = get_payment_gateway(txn.provider_slug)
        gateway.finalize(txn, request)
        create_shipment_for_order(txn.order)
        try:
            from core.utils import send_order_confirmation

            send_order_confirmation(txn.order, request)
        except Exception:
            pass
        messages.success(request, 'Payment successful.')
        return redirect('orders:order_detail', order_id=txn.order_id)


class PaymentCancelView(View):
    def get(self, request, order_id):
        order = get_accessible_order(request, order_id)
        if order is None:
            messages.error(request, 'Access denied.')
            return redirect('accounts:login')
        messages.warning(request, 'Payment was cancelled. You can try again anytime.')
        return redirect('integrations:payment_checkout', order_id=order.id)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request):
        from django.conf import settings

        secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        if not secret:
            return HttpResponse('Webhook not configured', status=501)

        import stripe

        payload = request.body
        sig = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        try:
            event = stripe.Webhook.construct_event(payload, sig, secret)
        except Exception:
            return HttpResponseBadRequest('Invalid signature')

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            txn = PaymentTransaction.objects.filter(external_id=session['id']).first()
            if txn and txn.status != 'succeeded':
                txn.mark_succeeded(external_id=session['id'], raw=dict(session))
                create_shipment_for_order(txn.order)

        return HttpResponse(status=200)
