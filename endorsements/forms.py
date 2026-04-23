from django import forms
from .models import Endorsement
from leaders.models import Leader
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset, HTML

User = get_user_model()


class EndorsementForm(forms.ModelForm):
    class Meta:
        model = Endorsement
        fields = (
            'user', 'member_full_name', 'member_id_number',
            'endorsement_type', 'subject', 'addressed_to', 'addressed_to_address',
            'purpose', 'member_standing', 'body',
            'related_service_request', 'valid_from', 'valid_until',
            'issued_by', 'issued_by_name', 'issued_by_role',
        )
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
            'member_standing': forms.Textarea(attrs={'rows': 3}),
            'addressed_to_address': forms.Textarea(attrs={'rows': 2}),
            'purpose': forms.Textarea(attrs={'rows': 2}),
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['issued_by'].queryset = Leader.objects.filter(is_active=True)
        self.fields['user'].required = False
        self.fields['related_service_request'].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<p class="text-muted small"><i class="bi bi-info-circle"></i> '
                 'All fields marked * are required. The endorsement will be generated as a PDF with the KCK letterhead once you click Publish.</p>'),
            Fieldset('Member Being Endorsed',
                Row(Column('user', css_class='col-md-6'), Column('member_id_number', css_class='col-md-6')),
                'member_full_name',
            ),
            Fieldset('Letter Details',
                Row(Column('endorsement_type', css_class='col-md-6'),
                    Column('related_service_request', css_class='col-md-6')),
                'subject',
                Row(Column('addressed_to', css_class='col-md-12')),
                'addressed_to_address',
                'purpose',
            ),
            Fieldset('Letter Body',
                HTML('<small class="text-muted d-block mb-2">Describe the member\'s standing and include the main endorsement statement.</small>'),
                'member_standing',
                'body',
            ),
            Fieldset('Validity',
                Row(Column('valid_from', css_class='col-md-6'),
                    Column('valid_until', css_class='col-md-6')),
            ),
            Fieldset('Issuer',
                'issued_by',
                Row(Column('issued_by_name', css_class='col-md-6'),
                    Column('issued_by_role', css_class='col-md-6')),
            ),
        )
        self.helper.add_input(Submit('submit', 'Save as Draft', css_class='btn-primary btn-lg'))


class QuickEndorsementFromRequestForm(forms.Form):
    """Minimal form to quickly generate a cover note from an embassy service request."""
    endorsement_type = forms.ChoiceField(
        choices=[
            ('cover_note', 'Cover Note'),
            ('endorsement', 'Letter of Endorsement'),
            ('introduction', 'Letter of Introduction'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='cover_note',
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='e.g. "Cover Note for Passport Renewal Application"',
    )
    addressed_to = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'e.g. The Ambassador, Kenyan Embassy in Seoul'}),
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        help_text='Main body of the endorsement letter',
    )
