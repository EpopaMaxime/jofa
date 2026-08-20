from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Product
from vendors.models import Vendor


class Command(BaseCommand):
    help = 'Create JOFA Official vendor and attach orphan products'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='jofa_official',
            defaults={
                'email': 'vendors@jofa.local',
                'first_name': 'JOFA',
                'last_name': 'Official',
                'is_staff': False,
            },
        )
        if created:
            user.set_password('ChangeMeVendor123!')
            user.save()
            self.stdout.write('Created user jofa_official / ChangeMeVendor123!')

        vendor, v_created = Vendor.objects.update_or_create(
            user=user,
            defaults={
                'store_name': 'JOFA Official',
                'slug': 'jofa-official',
                'tagline': 'Botanical purity & clinical excellence',
                'description': 'Official JOFA marketplace storefront.',
                'email': user.email,
                'city': 'Douala',
                'country': 'Cameroon',
                'status': 'approved',
                'is_active': True,
                'is_featured': True,
                'commission_rate': 0,
            },
        )
        attached = Product.objects.filter(vendor__isnull=True).update(vendor=vendor)
        self.stdout.write(self.style.SUCCESS(
            f"Vendor {'created' if v_created else 'updated'}: {vendor.store_name}. "
            f'Attached {attached} product(s).'
        ))
