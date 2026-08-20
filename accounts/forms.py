from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone', 'address', 'city', 'country']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
            'address': forms.Textarea(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
            'country': forms.TextInput(attrs={'class': 'w-full border border-gray-100 p-4 font-light text-sm outline-none focus:border-jofa-gold transition-colors'}),
        }

class CustomRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(max_length=20, required=False, label="Phone Number")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label="Street Address")
    city = forms.CharField(max_length=100, required=False, label="City")
    country = forms.CharField(max_length=100, required=False, label="Country")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data.get('phone', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.city = self.cleaned_data.get('city', '')
            profile.country = self.cleaned_data.get('country', '')
            profile.save()
        return user
