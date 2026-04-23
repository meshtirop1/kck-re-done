from django import forms
from .models import EmbassyServiceRequest, RequestNote, SERVICE_TYPE_CHOICES, REQUEST_STATUS_CHOICES
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset, HTML


class EmbassyServiceRequestForm(forms.ModelForm):
    class Meta:
        model = EmbassyServiceRequest
        fields = (
            'service_type', 'priority',
            'full_name', 'kenyan_id_number', 'current_document_number',
            'date_of_birth', 'place_of_birth',
            'phone', 'korean_phone', 'address_in_korea', 'city',
            'purpose', 'urgency_reason', 'preferred_appointment_date',
            'supporting_document_1', 'supporting_document_2', 'supporting_document_3',
            'consent_data_sharing', 'consent_privacy_policy',
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'preferred_appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'address_in_korea': forms.Textarea(attrs={'rows': 2}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
            'urgency_reason': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        city_choices = [
            ('', 'Select city'),
            ('seoul', 'Seoul'), ('busan', 'Busan'), ('incheon', 'Incheon'),
            ('daegu', 'Daegu'), ('daejeon', 'Daejeon'), ('gwangju', 'Gwangju'),
            ('other', 'Other'),
        ]
        self.fields['city'] = forms.ChoiceField(choices=city_choices, required=False)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info mb-4"><i class="bi bi-info-circle"></i> '
                 '<strong>KCK is a facilitator, not the embassy.</strong> '
                 'We help coordinate your request with the Kenyan Embassy in Seoul. '
                 'Official processing, approval, and document issuance is done by the embassy.</div>'),
            Fieldset('Service Needed',
                Row(Column('service_type', css_class='col-md-8'), Column('priority', css_class='col-md-4')),
            ),
            Fieldset('Your Information (as per Kenyan ID)',
                Row(Column('full_name', css_class='col-md-12')),
                Row(Column('kenyan_id_number', css_class='col-md-6'), Column('current_document_number', css_class='col-md-6')),
                Row(Column('date_of_birth', css_class='col-md-6'), Column('place_of_birth', css_class='col-md-6')),
            ),
            Fieldset('Contact in Korea',
                Row(Column('phone', css_class='col-md-6'), Column('korean_phone', css_class='col-md-6')),
                Row(Column('city', css_class='col-md-4'), Column('address_in_korea', css_class='col-md-8')),
            ),
            Fieldset('Purpose of Request',
                'purpose', 'urgency_reason', 'preferred_appointment_date',
            ),
            Fieldset('Supporting Documents',
                HTML('<p class="text-muted small">Upload scanned copies of relevant documents. '
                     'Accepted formats: PDF, JPG, PNG (max 10MB each).</p>'),
                Row(Column('supporting_document_1', css_class='col-md-12')),
                Row(Column('supporting_document_2', css_class='col-md-12')),
                Row(Column('supporting_document_3', css_class='col-md-12')),
            ),
            Fieldset('Consent & Privacy',
                HTML('<p class="small">By submitting this request, you agree to:'),
                'consent_data_sharing',
                'consent_privacy_policy',
                HTML('<p class="text-muted small mt-2">Read our <a href="/privacy/" target="_blank">Privacy Policy</a> '
                     'and <a href="/data-handling/" target="_blank">Data Handling Statement</a>.</p>'),
            ),
        )
        self.helper.add_input(Submit('submit', 'Submit Request', css_class='btn-danger btn-lg'))

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('consent_data_sharing'):
            self.add_error('consent_data_sharing', 'You must consent to data sharing with the embassy to submit this request.')
        if not cleaned.get('consent_privacy_policy'):
            self.add_error('consent_privacy_policy', 'You must agree to the privacy policy to submit this request.')
        return cleaned


class RequestNoteForm(forms.ModelForm):
    class Meta:
        model = RequestNote
        fields = ('message', 'attachment')
        widgets = {'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn-primary'))


class RequestStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=REQUEST_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}))
    embassy_reference = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Embassy reference (if forwarded)'}))
    message_to_member = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional message to the member about this status change'}))
    internal_note = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Internal note (not visible to member)'}))


class AssignOfficerForm(forms.Form):
    officer = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='-- Unassign --',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['officer'].queryset = User.objects.filter(
            leader_profile__isnull=False, leader_profile__is_active=True
        ).distinct()
