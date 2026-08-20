from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect

from .models import Vendor


def get_vendor_or_none(user):
    if not user.is_authenticated:
        return None
    return getattr(user, 'vendor', None)


class VendorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require an approved, active vendor account."""

    def test_func(self):
        vendor = get_vendor_or_none(self.request.user)
        return bool(vendor and vendor.is_selling)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        vendor = get_vendor_or_none(self.request.user)
        if vendor and vendor.status == 'pending':
            return redirect('vendors:pending')
        if vendor and vendor.status == 'suspended':
            return redirect('vendors:suspended')
        return redirect('vendors:register')

    def get_vendor(self) -> Vendor:
        vendor = get_vendor_or_none(self.request.user)
        if not vendor or not vendor.is_selling:
            raise PermissionDenied
        return vendor


def vendor_owns_product(vendor, product):
    return product.vendor_id == vendor.id
