import os
import sys
import django

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jofa_brand.settings')
django.setup()

from blog.models import Post

mapping = {
    "The Ultimate Morning Ritual for Radiant Skin": "blog/morning_ritual.jpg",
    "Tropical Skincare: Mastering the Cameroon Climate": "blog/tropical_care.jpg",
    "Understanding Your Skin Type: The Foundation of Care": "blog/skin_types.jpg",
    "The Science of Botanical Purity": "blog/botanical_science.jpg",
    "Nighttime Restoration: The Healing Hours": "blog/night_repair.jpg",
    "Soothing the storm: Managing Skin Irritation Naturally": "blog/skin_soothing.jpg",
    "Soothing the Storm: Managing Skin Irritation Naturally": "blog/skin_soothing.jpg" # Handle case
}

for title, img_path in mapping.items():
    Post.objects.filter(title=title).update(image=img_path)
    print(f"Updated image for: {title}")

print("Successfully updated all guide images with meaningful visuals!")
