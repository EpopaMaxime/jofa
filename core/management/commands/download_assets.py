import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product
from blog.models import Post
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Downloads remote Unsplash images to local media folder and updates models'

    def handle(self, *args, **kwargs):
        self.stdout.write('Downloading assets...')
        
        # Product Images
        product_images = [
            'https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1612817288484-6f916006741a?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1590156221170-28a179df754d?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1556228578-0d85ec019d14?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1601049541289-9b1b7abcfe19?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1556228578-c87baec7b71f?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1594125355930-36a6ecdae02a?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?q=80&w=800&auto=format&fit=crop'
        ]
        
        products = Product.objects.all()
        for i, product in enumerate(products):
            if i < len(product_images):
                self.download_and_save(product, 'image', product_images[i], f'product_{product.id}.jpg')

        # Blog Images
        blog_images = [
            'https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1552046122-03184de85e08?q=80&w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?q=80&w=800&auto=format&fit=crop'
        ]
        
        posts = Post.objects.all()
        for i, post in enumerate(posts):
            if i < len(blog_images):
                self.download_and_save(post, 'image', blog_images[i], f'blog_{post.id}.jpg')

        # Hero Images (to media/hero/)
        hero_images = [
            'https://images.unsplash.com/photo-1556228578-0d85ec019d14?q=80&w=2000&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1590156221170-28a179df754d?q=80&w=2000&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=2000&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1596462502278-27bfdc4033c8?q=80&w=2000&auto=format&fit=crop'
        ]
        
        hero_dir = os.path.join(settings.MEDIA_ROOT, 'hero')
        if not os.path.exists(hero_dir):
            os.makedirs(hero_dir)
            
        for i, url in enumerate(hero_images):
            hero_path = os.path.join(hero_dir, f'hero_{i+1}.jpg')
            if os.path.exists(hero_path):
                self.stdout.write(f'hero_{i+1}.jpg already exists, skipping.')
                continue
                
            try:
                self.stdout.write(f'Downloading hero {i+1} from {url}...')
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    with open(hero_path, 'wb') as f:
                        f.write(response.content)
                    self.stdout.write(self.style.SUCCESS(f'Saved hero_{i+1}.jpg'))
                else:
                    self.stdout.write(self.style.ERROR(f'Status {response.status_code} for hero {i+1}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to download hero {url}: {e}'))

        self.stdout.write(self.style.SUCCESS('Assets localized successfully!'))

    def download_and_save(self, instance, field_name, url, filename):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                getattr(instance, field_name).save(filename, ContentFile(response.content), save=True)
                self.stdout.write(f'Saved {filename} for {instance}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to download {url}: {e}'))
