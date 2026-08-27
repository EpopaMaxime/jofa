from django.shortcuts import get_object_or_404

from .models import Order


def user_can_access_order(request, order):
    if request.user.is_authenticated:
        if request.user.is_staff or order.user_id == request.user.id:
            return True
    guest_ids = request.session.get('guest_order_ids') or []
    try:
        return int(order.id) in [int(i) for i in guest_ids]
    except (TypeError, ValueError):
        return False


def remember_guest_order(request, order):
    ids = [int(i) for i in (request.session.get('guest_order_ids') or [])]
    if order.id not in ids:
        ids.append(order.id)
        request.session['guest_order_ids'] = ids
        request.session.modified = True


def get_accessible_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not user_can_access_order(request, order):
        return None
    return order
