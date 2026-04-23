from django import forms
from .models import VisaApplication, PassportApplication
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset, HTML

class VisaApplicationForm(forms.ModelForm):
    class Meta:
        model = VisaApplication
        fields = ('visa_type', 'full_name', 'date_of_birth', 'nationality', 'passport_number',
                  'phone', 'address', 'purpose_of_visit', 'intended_arrival', 'intended_departure',
                  'supporting_document')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'intended_arrival': forms.DateInput(attrs={'type': 'date'}),
            'intended_departure': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'purpose_of_visit': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active visa types
        from .models import VisaType
        self.fields['visa_type'].queryset = VisaType.objects.filter(active=True)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Visa Information', 'visa_type'),
            Fieldset('Personal Information',
                Row(Column('full_name', css_class='col-md-6'), Column('date_of_birth', css_class='col-md-6')),
                Row(Column('nationality', css_class='col-md-6'), Column('passport_number', css_class='col-md-6')),
                Row(Column('phone', css_class='col-md-12')),
                'address',
            ),
            Fieldset('Trip Details',
                'purpose_of_visit',
                Row(Column('intended_arrival', css_class='col-md-6'), Column('intended_departure', css_class='col-md-6')),
            ),
            Fieldset('Supporting Documents', 'supporting_document',
                HTML('<small class="text-muted">Upload a single PDF with all your documents (passport, photos, bank statement, etc.)</small>')),
        )
        self.helper.add_input(Submit('submit', 'Submit Application', css_class='btn-danger btn-lg'))

    def clean(self):
        cleaned = super().clean()
        arrival = cleaned.get('intended_arrival')
        departure = cleaned.get('intended_departure')
        if arrival and departure and departure < arrival:
            raise forms.ValidationError("Departure date must be after arrival date.")
        return cleaned

class PassportApplicationForm(forms.ModelForm):
    class Meta:
        model = PassportApplication
        fields = ('type', 'full_name', 'date_of_birth', 'place_of_birth', 'gender', 'national_id',
                  'current_passport_number', 'phone', 'email', 'address_in_korea', 'address_in_kenya',
                  'supporting_document')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address_in_korea': forms.Textarea(attrs={'rows': 3}),
            'address_in_kenya': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Application Type', 'type'),
            Fieldset('Personal Information',
                Row(Column('full_name', css_class='col-md-6'), Column('date_of_birth', css_class='col-md-6')),
                Row(Column('place_of_birth', css_class='col-md-6'), Column('gender', css_class='col-md-6')),
                Row(Column('national_id', css_class='col-md-6'), Column('current_passport_number', css_class='col-md-6')),
                Row(Column('phone', css_class='col-md-6'), Column('email', css_class='col-md-6')),
            ),
            Fieldset('Addresses',
                'address_in_korea',
                'address_in_kenya',
            ),
            Fieldset('Supporting Documents', 'supporting_document'),
        )
        self.helper.add_input(Submit('submit', 'Submit Application', css_class='btn-danger btn-lg'))

class ApplicationStatusUpdateForm(forms.Form):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('additional_info_needed', 'Additional Info Needed'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    admin_notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)
