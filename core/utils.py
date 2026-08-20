from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

def send_order_confirmation(order, request=None):
    subject = f'Your JOFA Essence Order #{order.id} is Confirmed'
    domain = get_current_site(request).domain if request else 'jofaessence.com'
    protocol = 'https' if request and request.is_secure() else 'http'
    
    # Send to Customer
    customer_context = {
        'order': order,
        'domain': domain,
        'protocol': protocol,
        'is_admin': False,
    }
    customer_html = render_to_string('email/order_confirmation.html', customer_context)
    customer_text = strip_tags(customer_html)
    
    msg = EmailMultiAlternatives(
        subject,
        customer_text,
        settings.DEFAULT_FROM_EMAIL,
        [order.email]
    )
    msg.attach_alternative(customer_html, "text/html")
    msg.send()
    
    # Send to Admin
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    admin_subject = f'[NEW ORDER] #{order.id} - {order.first_name} {order.last_name}'
    admin_context = {
        'order': order,
        'domain': domain,
        'protocol': protocol,
        'is_admin': True,
    }
    admin_html = render_to_string('email/order_confirmation.html', admin_context)
    admin_text = strip_tags(admin_html)
    
    admin_msg = EmailMultiAlternatives(
        admin_subject,
        admin_text,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email]
    )
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()

def send_contact_notification(message, request=None):
    domain = get_current_site(request).domain if request else 'jofaessence.com'
    protocol = 'https' if request and request.is_secure() else 'http'
    
    # Send to Customer (Thank You)
    customer_subject = f'Message Received: {message.subject}'
    customer_context = {
        'message': message,
        'domain': domain,
        'protocol': protocol,
        'is_admin': False,
    }
    customer_html = render_to_string('email/contact_notification.html', customer_context)
    customer_text = strip_tags(customer_html)
    
    msg = EmailMultiAlternatives(
        customer_subject,
        customer_text,
        settings.DEFAULT_FROM_EMAIL,
        [message.email]
    )
    msg.attach_alternative(customer_html, "text/html")
    msg.send()

    # Send to Admin
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    admin_subject = f'[INQUIRY] {message.subject} - {message.name}'
    admin_context = {
        'message': message,
        'domain': domain,
        'protocol': protocol,
        'is_admin': True,
    }
    admin_html = render_to_string('email/contact_notification.html', admin_context)
    admin_text = strip_tags(admin_html)
    
    admin_msg = EmailMultiAlternatives(
        admin_subject,
        admin_text,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email]
    )
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()
