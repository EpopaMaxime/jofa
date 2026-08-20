from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from products.models import Category, Product, ProductImage
from .models import Vendor


class VendorRegistrationForm(UserCreationForm):
    store_name = forms.CharField(max_length=160, label='Store name')
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=False)
    city = forms.CharField(max_length=100, required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label='About your brand',
    )
    accept_terms = forms.BooleanField(
        label='I agree to the marketplace seller terms',
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
            'store_name',
            'phone',
            'city',
            'description',
            'accept_terms',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Vendor.objects.create(
                user=user,
                store_name=self.cleaned_data['store_name'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data.get('phone', ''),
                city=self.cleaned_data.get('city', ''),
                description=self.cleaned_data.get('description', ''),
                status='approved',
                is_active=True,
            )
        return user


class VendorOpenStoreForm(forms.ModelForm):
    """Existing customer opens a seller store (no new user)."""

    accept_terms = forms.BooleanField(label='I agree to the marketplace seller terms')

    class Meta:
        model = Vendor
        fields = ['store_name', 'phone', 'city', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'store_name',
            'tagline',
            'description',
            'logo',
            'banner',
            'email',
            'phone',
            'address',
            'city',
            'country',
        ]


class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category',
            'name',
            'image',
            'price',
            'discount_percentage',
            'description',
            'ingredients',
            'skin_type',
            'stock',
            'available',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'ingredients': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
