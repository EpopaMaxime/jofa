from django import forms
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


class ConsultationPhotoForm(forms.ModelForm):
    class Meta:
        model = ConsultationPhoto
        fields = ['image', 'angle']
        widgets = {
            'image': forms.ClearableFileInput(
                attrs={'class': INPUT_CLASS, 'accept': 'image/*'}
            ),
            'angle': forms.Select(attrs={'class': INPUT_CLASS}),
        }
