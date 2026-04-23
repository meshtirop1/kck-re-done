from django import forms
from .models import SellerProfile, Product, ProductCategory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset, HTML


class SellerApplicationForm(forms.ModelForm):
    accepts_terms = forms.BooleanField(
        required=True,
        label='I agree to the KCK Kenyan Market terms: I will only sell authentic, legal products, respond to buyers promptly, and uphold community standards.'
    )

    class Meta:
        model = SellerProfile
        fields = (
            'business_name', 'bio', 'profile_photo',
            'whatsapp_number', 'phone', 'email_contact',
            'city', 'location_notes',
        )
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4,
                'placeholder': 'Tell buyers about your business — what do you sell, how long have you been in Korea, etc.'}),
            'location_notes': forms.TextInput(attrs={
                'placeholder': 'e.g. "Near Itaewon Station" — helps buyers plan pickups'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info"><i class="bi bi-info-circle"></i> '
                 'Your application will be reviewed by a KCK leader. This usually takes 1–3 days. '
                 'Once approved, you can start listing products.</div>'),
            Fieldset('Your Business',
                'business_name', 'bio', 'profile_photo',
            ),
            Fieldset('Contact',
                Row(Column('whatsapp_number', css_class='col-md-6'),
                    Column('phone', css_class='col-md-6')),
                'email_contact',
            ),
            Fieldset('Location',
                Row(Column('city', css_class='col-md-4'),
                    Column('location_notes', css_class='col-md-8')),
            ),
            'accepts_terms',
        )
        self.helper.add_input(Submit('submit', 'Submit Application',
            css_class='btn-danger btn-lg'))


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'name', 'category', 'description', 'image',
            'price', 'currency',
            'free_delivery_korea', 'delivery_option', 'delivery_notes', 'city',
            'whatsapp_link_override', 'whatsapp_message_template',
            'is_available',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
            'whatsapp_message_template': forms.TextInput(attrs={
                'placeholder': "Optional: Hi! I'm interested in your product..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ProductCategory.objects.filter(active=True)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Fieldset('Product details',
                'name', 'category', 'description', 'image',
            ),
            Fieldset('Price',
                Row(Column('price', css_class='col-md-8'),
                    Column('currency', css_class='col-md-4')),
            ),
            Fieldset('Delivery',
                HTML('<p class="text-muted small">Tell buyers how they can get the product.</p>'),
                'free_delivery_korea',
                Row(Column('delivery_option', css_class='col-md-6'),
                    Column('city', css_class='col-md-6')),
                'delivery_notes',
            ),
            Fieldset('WhatsApp contact (optional)',
                HTML('<p class="text-muted small">Defaults to your seller WhatsApp. Override only if you want a different contact for this product.</p>'),
                'whatsapp_link_override',
                'whatsapp_message_template',
            ),
            'is_available',
        )
        self.helper.add_input(Submit('submit', 'Save Product',
            css_class='btn-primary btn-lg'))


class SellerReviewForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[('approved', '✓ Approve seller'), ('rejected', '✗ Reject application')],
        widget=forms.RadioSelect,
        label='Decision',
    )
    notes = forms.CharField(
        required=False,
        label='Notes',
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control',
            'placeholder': 'Internal notes or rejection reason (visible to the applicant if rejecting)'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit(
            'submit', 'Submit Decision',
            css_class='btn-primary btn-lg w-100 fw-bold mt-2',
        ))
