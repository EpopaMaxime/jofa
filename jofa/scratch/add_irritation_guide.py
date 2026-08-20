import os
import sys
import django
from django.utils.text import slugify

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jofa_brand.settings')
django.setup()

from blog.models import Post

# Add Skin Irritation Guide
title = "Soothing the Storm: Managing Skin Irritation Naturally"
excerpt = "Redness, itching, and inflammation can disrupt your peace. Discover the botanical path to calm and restored skin."
content = """When your skin becomes irritated, it's often a signal that your delicate moisture barrier has been compromised. Whether caused by environmental stressors, harsh products, or the intense tropical sun, the key to recovery is patience and gentle botanical care.

The Soothing Ritual:
1. Immediate Cooling: Use a cold compress or a mineral-rich mist to reduce heat and inflammation.
2. Botanical Calm: Look for ingredients like Aloe Vera, Chamomile, and Centella Asiatica (Cica). These 'green' ingredients are nature's most powerful anti-inflammatories.
3. Barrier Repair: Apply a moisturizer with ceramides and niacinamide to help rebuild your skin's natural shield.
4. Less is More: When irritated, stop using exfoliants, retinoids, or heavy fragrances. Focus on the essentials until your skin returns to its natural state.

At JOFA, our soothing essences are formulated to respect your skin's sensitivity while providing the deep nourishment it needs to heal. Peace for your mind starts with peace for your skin."""

# Create the post
Post.objects.create(
    title=title,
    slug=slugify(title),
    excerpt=excerpt,
    content=content,
    image="blog/blog_4.jpg" # Using a placeholder for now
)

print(f"Created new guide: {title}")
