from django import forms
from .models import EventRegistration
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ('notes',)
        widgets = {'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any special requirements or notes? (optional)'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Register for Event', css_class='btn-danger btn-lg w-100'))
