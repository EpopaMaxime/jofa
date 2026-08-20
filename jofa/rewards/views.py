from django.shortcuts import render
from .models import LoyaltyTier, EarnMethod

def loyalty_program(request):
    tiers = LoyaltyTier.objects.all().prefetch_related('benefits')
    earn_methods = EarnMethod.objects.all()
    context = {
        'tiers': tiers,
        'earn_methods': earn_methods,
    }
    return render(request, 'rewards/loyalty.html', context)
