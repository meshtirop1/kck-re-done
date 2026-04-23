from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, HTML as CrispyHTML

from .models import Communication, Announcement


class CommunicationForm(forms.ModelForm):
    class Meta:
        model = Communication
        fields = [
            'subject', 'category', 'audience', 'audience_filter',
            'sender', 'sender_name_override', 'sender_role_override',
            'cover_image', 'body',
        ]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 12}),
            'audience_filter': forms.TextInput(attrs={'placeholder': 'e.g. seoul, student'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Fieldset(
                'Communication Details',
                'subject',
                Row(
                    Column('category', css_class='col-md-6'),
                    Column('audience', css_class='col-md-6'),
                ),
                'audience_filter',
            ),
            Fieldset(
                'Sender',
                'sender',
                Row(
                    Column('sender_name_override', css_class='col-md-6'),
                    Column('sender_role_override', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Content',
                'cover_image',
                'body',
            ),
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'category', 'excerpt', 'body',
            'cover_image', 'is_published', 'is_pinned',
        ]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 12}),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Fieldset(
                'Announcement',
                'title',
                Row(
                    Column('category', css_class='col-md-6'),
                    Column('cover_image', css_class='col-md-6'),
                ),
                'excerpt',
                'body',
                Row(
                    Column('is_published', css_class='col-md-6'),
                    Column('is_pinned', css_class='col-md-6'),
                ),
            ),
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )
