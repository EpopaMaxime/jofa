"""Lightweight JSON API surface for future mobile / partner expansion."""

from django.http import JsonResponse
from django.views import View

from recommendations.engine import RecommendationEngine
from recommendations.models import SkinConcern
from integrations.models import IntegrationProvider


class ConcernsAPIView(View):
    def get(self, request):
        data = list(
            SkinConcern.objects.filter(is_active=True).values(
                'code', 'name', 'description', 'severity_weight'
            )
        )
        return JsonResponse({'concerns': data})


class RecommendAPIView(View):
    def get(self, request):
        codes = [c for c in request.GET.get('concerns', '').split(',') if c]
        skin_type = request.GET.get('skin_type') or None
        engine = RecommendationEngine()
        products = engine.products_for_concerns(codes, skin_type=skin_type)
        routines = engine.routines_for_profile(codes, skin_type=skin_type)
        return JsonResponse(
            {
                'products': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'slug': p.slug,
                        'price': str(p.get_discounted_price),
                        'url': p.get_absolute_url(),
                    }
                    for p in products
                ],
                'routines': [
                    {
                        'id': r.id,
                        'name': r.name,
                        'slug': r.slug,
                        'steps': [
                            {
                                'order': s.order,
                                'type': s.step_type,
                                'product_id': s.product_id,
                                'product': s.product.name,
                            }
                            for s in r.steps.all()
                        ],
                    }
                    for r in routines
                ],
            }
        )


class ProvidersAPIView(View):
    def get(self, request):
        category = request.GET.get('category')
        qs = IntegrationProvider.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        return JsonResponse(
            {
                'providers': list(
                    qs.values('slug', 'name', 'category', 'is_default')
                )
            }
        )
