from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('products/', include('products.urls', namespace='products')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('blog/', include('blog.urls', namespace='blog')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('consult/', include('consultation.urls', namespace='consultation')),
    path('integrations/', include('integrations.urls', namespace='integrations')),
    path('sell/', include('vendors.urls', namespace='vendors')),
    path('', include('core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
