import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Category, Product
from blog.models import Post
from core.models import FAQ, Partner, TeamMember
from reviews.models import Review

class Command(BaseCommand):
    help = 'Generates sample data for JOFA brand'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample data...')

        # Categories
        cleansers, _ = Category.objects.update_or_create(name='Cleansers', defaults={'description': 'Gentle cleansing rituals to purify and prepare your canvas.'})
        serums, _ = Category.objects.update_or_create(name='Serums', defaults={'description': 'Concentrated botanical elixirs for targeted skin transformation.'})
        moisturizers, _ = Category.objects.update_or_create(name='Moisturizers', defaults={'description': 'Deep hydration for a supple, luminous complexion.'})
        masks, _ = Category.objects.update_or_create(name='Masks', defaults={'description': 'Weekly rituals for restorative skin recovery.'})
        essentials, _ = Category.objects.update_or_create(name='Essentials', defaults={'description': 'The fundamental building blocks of a professional skincare routine.'})

        # Products
        v_milk, _ = Product.objects.update_or_create(
            name='Velvet Milk Cleanser',
            defaults={
                'category': cleansers,
                'price': 32.00,
                'description': 'A luxurious, milky emulsion that delicately lifts impurities while preserving the skin\'s natural moisture barrier. Infused with soothing botanical extracts to leave your skin soft and refreshed.',
                'ingredients': 'Organic Rose Water, Aloe Vera Leaf Juice, Sweet Almond Oil, Vitamin E, Roman Chamomile',
                'skin_type': 'sensitive',
                'stock': 50,
                'featured': True,
                'available': True
            }
        )

        rad_c, _ = Product.objects.update_or_create(
            name='Radiance Vitamin C Elixir',
            defaults={
                'category': serums,
                'price': 65.00,
                'description': 'A potent daily treatment to illuminate your complexion. This stable Vitamin C formula neutralizes free radicals and boosts collagen production for a visible, youthful glow.',
                'ingredients': '15% Pure Vitamin C (L-Ascorbic Acid), Ferulic Acid, Hyaluronic Acid, Kakadu Plum Extract',
                'skin_type': 'all',
                'stock': 30,
                'featured': True,
                'available': True
            }
        )

        cloud_dew, _ = Product.objects.update_or_create(
            name='Cloud Dew Hydra Gel',
            defaults={
                'category': moisturizers,
                'price': 48.00,
                'description': 'An ultra-lightweight gel cream that floods the skin with long-lasting hydration. Perfect for a dewy finish without any heavy residue.',
                'ingredients': 'Plant-Derived Squalane, Organic Cucumber Extract, Marine Algae, Pro-Vitamin B5',
                'skin_type': 'oily',
                'stock': 40,
                'featured': True,
                'available': True
            }
        )

        midnight_balm, _ = Product.objects.update_or_create(
            name='Midnight Recovery Balm',
            defaults={
                'category': masks,
                'price': 58.00,
                'description': 'A rich, intensive overnight mask designed to repair and nourish. Wake up to skin that is deeply hydrated, plumped, and visibly restored.',
                'ingredients': 'Lavender Oil, Evening Primrose, Shea Butter, Peptides, Bakuchiol',
                'skin_type': 'dry',
                'stock': 25,
                'featured': True,
                'available': True
            }
        )

        golden_oil, _ = Product.objects.update_or_create(
            name='Golden Hour Facial Oil',
            defaults={
                'category': moisturizers,
                'price': 72.00,
                'description': 'A precious blend of rare botanical oils that mimic the skin\'s natural sebum for ultimate absorption and a radiant, non-greasy glow.',
                'ingredients': 'Jojoba Oil, Rosehip Seed Oil, Sea Buckthorn, Pomegranate Seed Oil',
                'skin_type': 'combination',
                'stock': 35,
                'featured': True,
                'available': True
            }
        )

        ebony_serum, _ = Product.objects.update_or_create(
            name='Ebony Night Serum',
            defaults={
                'category': serums,
                'price': 85.00,
                'description': 'A deep-acting nighttime serum specifically designed for high-end skin restoration. Contains rare onyx minerals and olive-derived antioxidants.',
                'ingredients': 'Onyx Mineral Complex, Olive Squalane, Retinol 0.5%, Ceramide NP',
                'skin_type': 'dry',
                'stock': 20,
                'featured': True,
                'available': True
            }
        )

        # Blog Posts
        Post.objects.update_or_create(
            title='The Art of the Double Cleanse',
            defaults={
                'content': 'Skincare is a ritual, not a chore. The double cleanse is the foundation of a healthy complexion. Start with an oil-based cleanser to melt away makeup and SPF, then follow with a water-based cleanser to deeply purify the pores. This ancient technique ensures your skin is perfectly prepared to absorb the active ingredients in your serums and moisturizers.',
                'excerpt': 'Master the multi-step cleansing ritual that Korean beauty experts swear by for clear, luminous skin.',
                'author': 'Elena Voss',
                'published': True
            }
        )

        Post.objects.update_or_create(
            title='Understanding the Skin Barrier',
            defaults={
                'content': 'Your skin barrier is your first line of defense against the world. When compromised, it leads to sensitivity, redness, and dehydration. In this article, we explore how to identify a damaged barrier and the botanical ingredients—like ceramides and squalane—that can help rebuild and protect it for a resilient, healthy glow.',
                'excerpt': 'Learn how to protect and repair your skin\'s most vital defense mechanism with pure, effective ingredients.',
                'author': 'Dr. Julian Rose',
                'published': True
            }
        )

        Post.objects.update_or_create(
            title='The Benefits of Cold-Pressed Oils',
            defaults={
                'content': 'Cold-pressing is the most effective way to extract the potent nutrients from botanical seeds without damaging their delicate chemical structure. At JOFA, we favor cold-pressed jojoba and rosehip oils for their unparalleled purity and efficacy.',
                'author': 'Sarah Chen',
                'published': True,
                'excerpt': 'Discover why the extraction method matters as much as the ingredient itself.'
            }
        )

        # Reviews
        users = []
        for uname in ['clara_beauty', 'marcus_glow', 'sophia_skin', 'ethan_pure', 'lily_ritual']:
            u, _ = User.objects.get_or_create(username=uname, defaults={'email': f'{uname}@example.com', 'first_name': uname.capitalize()})
            u.set_password('password123')
            u.save()
            users.append(u)

        review_texts = [
            "This cleanser changed my life. My skin feels like silk!",
            "Finally, a Vitamin C that doesn't irritate my sensitive skin. Highly recommend.",
            "The Midnight Recovery Balm is pure magic in a jar.",
            "I've tried many oils, but the Golden Hour Oil is by far the best for my combination skin.",
            "JOFA is the only brand I trust for my daily ritual. Incredible quality."
        ]

        prods = [v_milk, rad_c, midnight_balm, golden_oil, ebony_serum]
        for i, user in enumerate(users):
            Review.objects.update_or_create(
                user=user,
                product=prods[i % len(prods)],
                defaults={
                    'rating': random.randint(4, 5),
                    'comment': review_texts[i],
                    'approved': True
                }
            )

        # FAQs
        FAQ.objects.update_or_create(question='Are JOFA products safe for pregnancy?', defaults={'answer': 'Many of our products are pregnancy-safe as they focus on botanical ingredients. However, we always recommend consulting with your doctor before introducing new active ingredients like retinoids or high-concentration acids during pregnancy.', 'order': 1})
        FAQ.objects.update_or_create(question='How long does shipping take?', defaults={'answer': 'We ship within 24-48 hours of your order. Domestic shipping typically takes 3-5 business days, while international shipping can take 7-14 business days depending on the destination.', 'order': 2})
        FAQ.objects.update_or_create(question='Do you offer samples?', defaults={'answer': 'We include a complimentary selection of samples with every full-size product order so you can discover your next favorite JOFA ritual.', 'order': 3})

        # Partners
        Partner.objects.update_or_create(name='Eco-Luxe Beauty', defaults={'description': 'A premier distributor of sustainable and ethical luxury beauty products globally.', 'website': 'https://ecoluxe.com'})
        Partner.objects.update_or_create(name='Bloom Aesthetics', defaults={'description': 'High-end spa partners who integrate JOFA rituals into their professional treatments.', 'website': 'https://bloomaesthetics.com'})

        # Team Members
        TeamMember.objects.update_or_create(name='Elena Voss', defaults={'role': 'Founder & Creative Director', 'bio': 'With a background in botanical science and luxury design, Elena founded JOFA to bridge the gap between pure nature and high-end results.', 'order': 1})
        TeamMember.objects.update_or_create(name='Dr. Julian Rose', defaults={'role': 'Chief Dermatologist', 'bio': 'Dr. Rose ensures every JOFA formula is scientifically sound and clinically effective for all skin types.', 'order': 2})
        TeamMember.objects.update_or_create(name='Sarah Chen', defaults={'role': 'Head of Ritual Discovery', 'bio': 'Sarah travels the globe to source the rarest, most potent botanical ingredients for our collection.', 'order': 3})

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@jofabrand.com', 'admin123')
            self.stdout.write('Created superuser: admin / admin123')

        self.stdout.write(self.style.SUCCESS('Professional sample data generated successfully!'))
