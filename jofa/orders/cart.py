from decimal import Decimal
from django.conf import settings
from products.models import Product, Coupon

class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # store current coupon id
        self.coupon_id = self.session.get('coupon_id')
        # store applied points
        self.applied_points = self.session.get('applied_points', 0)

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    @property
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    def apply_coupon(self, coupon_code):
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            from django.utils import timezone
            now = timezone.now()
            if coupon.valid_from <= now <= coupon.valid_to:
                self.session['coupon_id'] = coupon.id
                self.coupon_id = coupon.id
                self.save()
                return True
        except Coupon.DoesNotExist:
            pass
        return False

    def apply_points(self, points):
        """
        Store the number of points the user wants to redeem.
        """
        self.session['applied_points'] = points
        self.applied_points = points
        self.save()

    def get_points_discount(self):
        """
        Calculate the monetary value of the applied points.
        """
        if self.applied_points:
            from rewards.models import RewardSetting
            setting = RewardSetting.objects.first()
            if setting and setting.points_to_cash_ratio:
                return Decimal(self.applied_points) * setting.points_to_cash_ratio
        return Decimal('0.00')


    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        coupon = self.coupon
        for item in cart.values():
            product = item['product']
            base_price = Decimal(item['price'])
            item['original_price'] = base_price
            
            if product.has_discount:
                item['price'] = Decimal(str(product.get_discounted_price))
                item['discount_applied'] = True
            else:
                item['price'] = base_price
                item['discount_applied'] = False

            # Apply coupon if applicable
            if coupon and coupon.is_valid():
                # If products are specified, check if this product is one of them
                if not coupon.products.exists() or product in coupon.products.all():
                    discount_factor = Decimal(1 - (coupon.discount / 100))
                    item['price'] = (item['price'] * discount_factor).quantize(Decimal('0.01'))
                    item['discount_applied'] = True

            item['total_price'] = item['price'] * item['quantity']
            item['original_total_price'] = item['original_price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Compute cart total, applying coupon discounts where applicable."""
        total = Decimal('0.00')
        coupon = self.coupon
        is_coupon_valid = coupon and coupon.is_valid()
        product_ids = self.cart.keys()
        products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}

        for product_id, item in self.cart.items():
            product = products.get(product_id)
            if not product:
                continue
            
            base_price = Decimal(item['price'])
            if product.has_discount:
                price = Decimal(str(product.get_discounted_price))
            else:
                price = base_price

            if is_coupon_valid:
                if not coupon.products.exists() or product in coupon.products.all():
                    price = (price * Decimal(1 - (coupon.discount / 100))).quantize(Decimal('0.01'))
            total += price * item['quantity']
        
        # Apply points discount
        points_discount = self.get_points_discount()
        return max(Decimal('0.00'), total - points_discount)

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        if 'applied_points' in self.session:
            del self.session['applied_points']
        self.save()
