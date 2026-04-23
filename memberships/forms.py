from django import forms
from .models import MembershipPayment, MembershipTier, MembershipBenefit


class DeclarePaymentForm(forms.ModelForm):
    class Meta:
        model = MembershipPayment
        fields = ['claimed_amount', 'claimed_date', 'proof_image', 'notes']
        widgets = {
            'claimed_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'claimed_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                'placeholder': 'Anything that helps the treasurer match your transfer (optional)'}),
            'proof_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'claimed_amount': 'Amount you sent',
            'claimed_date': 'Date of transfer',
            'proof_image': 'Transfer receipt / screenshot',
            'notes': 'Notes (optional)',
        }


class VerifyForm(forms.Form):
    action = forms.ChoiceField(choices=[('verify', 'Verify & activate'), ('reject', 'Reject')])
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False, label='Notes / reason')


class TierForm(forms.ModelForm):
    class Meta:
        model = MembershipTier
        fields = ['name', 'annual_amount', 'currency', 'description', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'annual_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BenefitForm(forms.ModelForm):
    class Meta:
        model = MembershipBenefit
        fields = ['title', 'description', 'icon', 'sort_order', 'active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-check-circle-fill'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BankSettingsForm(forms.Form):
    """Edits SiteSettings bank + membership fields (handled in view)."""
    bank_name = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    bank_account_name = forms.CharField(max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    bank_account_number = forms.CharField(max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    bank_branch = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    bank_swift = forms.CharField(max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    treasurer_contact_email = forms.EmailField(required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}))
    treasurer_contact_phone = forms.CharField(max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    membership_page_title = forms.CharField(max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    membership_page_intro = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
