from django import forms
from .models import TutorProfile, Subject

class TutorProfileForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = TutorProfile
        fields = [
            'title', 'name', 'email', 'phone', 'address', 'prof_pic', 'bio',
            'institution', 'qualification', 'subjects'
        ]
