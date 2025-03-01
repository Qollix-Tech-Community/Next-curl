from django import forms
from .models import StudentProfile, Subject

class StudentProfileForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = StudentProfile
        fields = [
            'name', 'email', 'phone', 'address', 'prof_pic', 'bio',
            'institution', 'qualification', 'subjects'
        ]
