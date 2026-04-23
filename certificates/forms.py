from django import forms
from .models import Certificate
from leaders.models import Leader
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ('recipient_user', 'recipient_name', 'cert_type', 'title', 'body',
                  'event_title', 'issued_date', 'issued_by', 'issued_by_name', 'issued_by_role')
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['issued_by'].queryset = Leader.objects.filter(is_active=True)
        self.fields['recipient_user'].required = False
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Recipient',
                Row(Column('recipient_user', css_class='col-md-6'), Column('recipient_name', css_class='col-md-6')),
            ),
            Fieldset('Certificate Details',
                Row(Column('cert_type', css_class='col-md-6'), Column('title', css_class='col-md-6')),
                'body',
                Row(Column('event_title', css_class='col-md-6'), Column('issued_date', css_class='col-md-6')),
            ),
            Fieldset('Issuer',
                'issued_by',
                Row(Column('issued_by_name', css_class='col-md-6'), Column('issued_by_role', css_class='col-md-6')),
            ),
        )
        self.helper.add_input(Submit('submit', 'Save Certificate', css_class='btn-primary'))


class VerifyCertificateForm(forms.Form):
    code = forms.CharField(label='Verification Code', max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g. KCK-CERT-2026-0001 or verification UUID'}))
