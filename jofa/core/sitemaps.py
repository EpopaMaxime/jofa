from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import Post
from products.models import Product

class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Post.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.updated_at

class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Product.objects.filter(available=True)

    def lastmod(self, obj):
        return obj.updated_at

class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = 'daily'

    def items(self):
        return ['core:home', 'products:product_list', 'blog:post_list']

    def location(self, item):
        try:
            return reverse(item)
        except:
            pass # handle missing views if any
        return '/'
