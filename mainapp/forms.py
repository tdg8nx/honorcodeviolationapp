from django import forms
from .models import HonorCodeViolation

class HonorCodeViolationForm(forms.ModelForm):
    class Meta:
        model = HonorCodeViolation
        widgets = {
            'date_of_incident': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        fields = ['name', 'date_of_incident', 'description', 'photo', 'file', 'class_name']