from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.forms.widgets import ClearableFileInput

from .models import SkinConsultation, ConsultationPhoto


INPUT_CLASS = (
    'w-full border border-gray-300 p-4 text-sm '
    'focus:outline-none focus:border-jofa-gold bg-jofa-beige'
)


class ConsultationStartForm(forms.ModelForm):
    class Meta:
        model = SkinConsultation
        fields = [
            'age_range',
            'declared_skin_type',
            'primary_goals',
            'sensitivity_level',
            'consent_analysis',
            'consent_image_retention',
        ]
        widgets = {
            'age_range': forms.Select(
                choices=[
                    ('', 'Select age range'),
                    ('under-18', 'Under 18'),
                    ('18-24', '18–24'),
                    ('25-34', '25–34'),
                    ('35-44', '35–44'),
                    ('45-54', '45–54'),
                    ('55+', '55+'),
                ],
                attrs={'class': INPUT_CLASS},
            ),
            'declared_skin_type': forms.Select(attrs={'class': INPUT_CLASS}),
            'primary_goals': forms.Textarea(
                attrs={
                    'rows': 4,
                    'class': INPUT_CLASS,
                    'placeholder': 'e.g. acne on cheeks, dullness, dark spots, dryness…',
                }
            ),
            'sensitivity_level': forms.NumberInput(
                attrs={'min': 1, 'max': 5, 'class': INPUT_CLASS}
            ),
        }

    def clean_consent_analysis(self):
        if not self.cleaned_data.get('consent_analysis'):
            raise forms.ValidationError(
                'You must consent to cosmetic skin analysis to continue.'
            )
        return self.cleaned_data['consent_analysis']


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(item, initial) for item in data]
        return [single(data, initial)]


class ConsultationPhotoForm(forms.Form):
    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={'class': INPUT_CLASS, 'accept': 'image/*', 'multiple': True}
        ),
        label='Photos',
    )
    angle = forms.ChoiceField(
        choices=ConsultationPhoto.ANGLE_CHOICES,
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
        initial='face',
    )

    def clean_images(self):
        files = self.files.getlist('images') if self.files else []
        cleaned = []
        for upload in files:
            if not isinstance(upload, UploadedFile):
                continue
            if not (upload.content_type or '').startswith('image/'):
                raise forms.ValidationError('Please select image files only (JPG, PNG, WEBP).')
            cleaned.append(upload)
        return cleaned
