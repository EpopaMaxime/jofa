from .models import Announcement

def announcements(request):
    return {
        'announcements': Announcement.objects.filter(active=True)
    }
