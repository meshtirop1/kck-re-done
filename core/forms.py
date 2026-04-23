from django import forms
from .models import ContactMessage
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column, Layout

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {'message': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('email', css_class='col-md-6')),
            'subject',
            'message',
        )
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn-primary btn-lg'))

class SearchForm(forms.Form):
    q = forms.CharField(max_length=200, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'}))
