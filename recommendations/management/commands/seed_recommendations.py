from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.text import slugify

from products.models import Category, Product
from recommendations.models import (
    ConcernProductMap,
    RoutineBundle,
    RoutineStep,
    SkinConcern,
)
from integrations.models import IntegrationProvider


DEFAULT_CONCERNS = [
    {
        'code': 'acne',
        'name': 'Acne & blemishes',
        'keywords': 'acne,pimple,breakout,blemish,spots',
        'related_skin_types': 'oily,combination',
        'severity_weight': 3,
        'description': 'Congestion, breakouts, and uneven texture.',
    },
    {
        'code': 'dehydration',
        'name': 'Dehydration',
        'keywords': 'dry,dehydrat,flaky,tight,moisture',
        'related_skin_types': 'dry,sensitive,combination',
        'severity_weight': 2,
        'description': 'Lack of water content leading to tightness or dullness.',
    },
    {
        'code': 'dullness',
        'name': 'Dullness',
        'keywords': 'dull,glow,radiance,tired,bright',
        'related_skin_types': 'all,dry,combination',
        'severity_weight': 2,
        'description': 'Loss of radiance and uneven luminosity.',
    },
    {
        'code': 'sensitivity',
        'name': 'Sensitivity',
        'keywords': 'sensitive,irritat,sting,react',
        'related_skin_types': 'sensitive',
        'severity_weight': 3,
        'description': 'Reactive or easily irritated skin.',
    },
    {
        'code': 'redness',
        'name': 'Redness',
        'keywords': 'red,redness,flush,inflame',
        'related_skin_types': 'sensitive',
        'severity_weight': 2,
        'description': 'Visible redness or flush-prone areas.',
    },
    {
        'code': 'excess-oil',
        'name': 'Excess oil',
        'keywords': 'oil,shine,sebum,greasy',
        'related_skin_types': 'oily,combination',
        'severity_weight': 2,
        'description': 'Overactive sebum and midday shine.',
    },
    {
        'code': 'uneven-tone',
        'name': 'Uneven tone',
        'keywords': 'dark spot,hyperpigment,tone,melasma,mark',
        'related_skin_types': 'all,combination,oily',
        'severity_weight': 3,
        'description': 'Dark spots and uneven pigmentation.',
    },
    {
        'code': 'barrier',
        'name': 'Barrier support',
        'keywords': 'barrier,repair,recover,compromise',
        'related_skin_types': 'sensitive,dry',
        'severity_weight': 2,
        'description': 'Compromised moisture barrier needing repair.',
    },
]


class Command(BaseCommand):
    help = 'Seed skin concerns, product maps, routines, and integration providers'

    def handle(self, *args, **options):
        self.stdout.write('Seeding recommendation + integration data...')
        concerns = {}
        for data in DEFAULT_CONCERNS:
            obj, _ = SkinConcern.objects.update_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'keywords': data['keywords'],
                    'related_skin_types': data['related_skin_types'],
                    'severity_weight': data['severity_weight'],
                    'description': data['description'],
                    'is_active': True,
                },
            )
            concerns[obj.code] = obj

        # Map products by skin_type + keyword heuristics on name/description
        products = list(Product.objects.filter(available=True))
        created_maps = 0
        for product in products:
            matched = set()
            blob = f'{product.name} {product.description} {product.ingredients}'.lower()
            for concern in concerns.values():
                if any(kw in blob for kw in concern.keyword_list()):
                    matched.add(concern.code)
            if not matched:
                defaults = {
                    'dry': ['dehydration'],
                    'oily': ['acne', 'excess-oil'],
                    'sensitive': ['sensitivity', 'barrier'],
                    'combination': ['dehydration', 'excess-oil'],
                }
                matched.update(defaults.get(product.skin_type, []))

            for idx, code in enumerate(sorted(matched)):
                _, was_created = ConcernProductMap.objects.update_or_create(
                    concern=concerns[code],
                    product=product,
                    defaults={
                        'priority': 5 + idx,
                        'role': self._guess_role(product),
                        'is_active': True,
                    },
                )
                if was_created:
                    created_maps += 1
            if matched:
                ConcernProductMap.objects.filter(product=product).exclude(
                    concern__code__in=matched
                ).update(is_active=False)
            else:
                ConcernProductMap.objects.filter(product=product).update(is_active=False)

        self._seed_routines(concerns)
        self._seed_providers()
        self.stdout.write(self.style.SUCCESS(
            f'Done. Concerns={len(concerns)}, new maps≈{created_maps}'
        ))

    def _guess_role(self, product):
        name = (product.name + ' ' + getattr(product.category, 'name', '')).lower()
        for role, words in [
            ('cleanser', ['cleanse', 'cleanser', 'wash', 'milk']),
            ('serum', ['serum', 'elixir', 'concentrate']),
            ('moisturizer', ['moistur', 'cream', 'lotion', 'butter']),
            ('mask', ['mask']),
            ('sunscreen', ['spf', 'sun', 'uv']),
            ('treatment', ['treatment', 'spot', 'acne', 'peel']),
        ]:
            if any(w in name for w in words):
                return role
        return 'other'

    def _seed_routines(self, concerns):
        defs = [
            {
                'name': 'Calm & Restore',
                'skin_type': 'sensitive',
                'concern_codes': ['sensitivity', 'barrier', 'redness'],
                'description': 'Gentle cleanse, barrier serum, and soothing moisturizer.',
            },
            {
                'name': 'Clarity Routine',
                'skin_type': 'oily',
                'concern_codes': ['acne', 'excess-oil'],
                'description': 'Purifying cleanse with targeted treatment and light hydration.',
            },
            {
                'name': 'Glow Essentials',
                'skin_type': 'all',
                'concern_codes': ['dullness', 'dehydration', 'uneven-tone'],
                'description': 'Daily radiance trio for luminous, balanced skin.',
            },
        ]
        for item in defs:
            routine, _ = RoutineBundle.objects.update_or_create(
                slug=slugify(item['name']),
                defaults={
                    'name': item['name'],
                    'skin_type': item['skin_type'],
                    'description': item['description'],
                    'is_active': True,
                    'featured': True,
                },
            )
            routine.concerns.set(
                [concerns[c] for c in item['concern_codes'] if c in concerns]
            )
            # Pick up to 3 products matching concerns
            product_ids = list(
                ConcernProductMap.objects.filter(
                    concern__code__in=item['concern_codes'], is_active=True
                )
                .order_by('priority')
                .values_list('product_id', flat=True)
            )
            seen = []
            for pid in product_ids:
                if pid not in seen:
                    seen.append(pid)
                if len(seen) >= 3:
                    break
            RoutineStep.objects.filter(routine=routine).delete()
            step_types = ['cleanser', 'serum', 'moisturizer']
            for order, pid in enumerate(seen, start=1):
                product = Product.objects.filter(id=pid).first()
                if not product:
                    continue
                RoutineStep.objects.create(
                    routine=routine,
                    product=product,
                    step_type=step_types[order - 1] if order <= 3 else 'other',
                    order=order,
                )

    def _seed_providers(self):
        providers = [
            ('cod', 'Cash on delivery', 'payment', True, True),
            ('stripe', 'Stripe', 'payment', True, False),
            ('simulate', 'Simulated Card (dev)', 'payment', True, False),
            ('manual', 'JOFA Manual Dispatch', 'delivery', True, True),
            ('mock_courier', 'Partner Courier (API-ready)', 'delivery', True, False),
            ('gmail-smtp', 'Gmail SMTP', 'email', True, True),
            ('newsletter', 'Marketing Newsletter Hook', 'marketing', False, False),
        ]
        for slug, name, category, active, default in providers:
            IntegrationProvider.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': category,
                    'is_active': active,
                    'is_default': default,
                    'notes': 'Seeded by seed_recommendations command',
                },
            )
        # Ensure only COD is default among payments
        IntegrationProvider.objects.filter(category='payment').exclude(slug='cod').update(
            is_default=False
        )
        IntegrationProvider.objects.filter(slug='cod').update(is_default=True, is_active=True)
