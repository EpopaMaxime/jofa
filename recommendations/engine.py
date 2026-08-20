from django.db.models import Q
from products.models import Product
from .models import ConcernProductMap, RoutineBundle, SkinConcern


class RecommendationEngine:
    """Match skin concerns / types to catalog products and routines."""

    def __init__(self, limit_per_concern=3, total_limit=8):
        self.limit_per_concern = limit_per_concern
        self.total_limit = total_limit

    def products_for_concerns(self, concern_codes, skin_type=None):
        codes = [c for c in concern_codes if c]
        maps = (
            ConcernProductMap.objects.filter(
                is_active=True,
                concern__is_active=True,
                concern__code__in=codes,
                product__available=True,
            )
            .select_related('product', 'concern')
            .order_by('priority', 'id')
        )

        seen = set()
        products = []
        for mapping in maps:
            if mapping.product_id in seen:
                continue
            seen.add(mapping.product_id)
            products.append(mapping.product)
            if len(products) >= self.total_limit:
                break

        if len(products) < self.total_limit:
            products.extend(
                self._fallback_by_skin_type(skin_type, seen, self.total_limit - len(products))
            )
        return products

    def _fallback_by_skin_type(self, skin_type, exclude_ids, limit):
        if limit <= 0:
            return []
        qs = Product.objects.filter(available=True).exclude(id__in=exclude_ids)
        if skin_type and skin_type != 'all':
            qs = qs.filter(Q(skin_type=skin_type) | Q(skin_type='all'))
        return list(qs.order_by('-featured', '-created_at')[:limit])

    def routines_for_profile(self, concern_codes=None, skin_type=None, limit=3):
        qs = RoutineBundle.objects.filter(is_active=True).prefetch_related(
            'steps__product', 'concerns'
        )
        if skin_type:
            qs = qs.filter(Q(skin_type=skin_type) | Q(skin_type='') | Q(skin_type='all'))
        if concern_codes:
            matched = qs.filter(concerns__code__in=concern_codes).distinct()
            if matched.exists():
                qs = matched
        return list(qs.order_by('-featured', 'name')[:limit])

    def complementary_for_product(self, product, limit=4):
        concern_ids = product.concern_maps.filter(is_active=True).values_list(
            'concern_id', flat=True
        )
        if concern_ids:
            maps = (
                ConcernProductMap.objects.filter(
                    concern_id__in=concern_ids,
                    is_active=True,
                    product__available=True,
                )
                .exclude(product=product)
                .select_related('product')
                .order_by('priority')
            )
            seen = set()
            out = []
            for m in maps:
                if m.product_id in seen:
                    continue
                seen.add(m.product_id)
                out.append(m.product)
                if len(out) >= limit:
                    return out
        return list(
            Product.objects.filter(
                available=True, category=product.category
            )
            .exclude(id=product.id)
            .order_by('-featured')[:limit]
        )

    def build_payload(self, concern_codes, skin_type=None):
        products = self.products_for_concerns(concern_codes, skin_type=skin_type)
        routines = self.routines_for_profile(concern_codes, skin_type=skin_type)
        concerns = list(
            SkinConcern.objects.filter(code__in=concern_codes, is_active=True)
        )
        return {
            'concerns': concerns,
            'products': products,
            'routines': routines,
        }
