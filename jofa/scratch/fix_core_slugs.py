import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jofa_brand.settings')
django.setup()

from core.models import TeamMember, NewsEvent
from django.utils.text import slugify

def fix_slugs():
    print("Fixing TeamMember slugs...")
    for member in TeamMember.objects.all():
        if not member.slug or member.slug == "None":
            member.slug = slugify(member.name)
            member.save()
            print(f"Fixed slug for Team Member: {member.name} -> {member.slug}")
    
    print("\nFixing NewsEvent slugs...")
    for item in NewsEvent.objects.all():
        if not item.slug or item.slug == "None":
            item.slug = slugify(item.title)
            item.save()
            print(f"Fixed slug for News/Event: {item.title} -> {item.slug}")

if __name__ == "__main__":
    fix_slugs()
