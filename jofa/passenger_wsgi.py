import os
import sys
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jofa_brand.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
