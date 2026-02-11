from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Individual


User = get_user_model()


class RegistrationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            css_class = "form-control"
            if name in ("address",):
                field.widget.attrs.setdefault("rows", 2)
            field.widget.attrs["class"] = css_class


    full_name = forms.CharField(max_length=200, required=True)
    national_number = forms.CharField(max_length=15, required=True)
    phone_number = forms.CharField(max_length=30, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)
    post_id = forms.CharField(max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2")

    def clean_national_number(self):
        national_number = (self.cleaned_data.get("national_number") or "").strip()
        if Individual.objects.filter(national_number=national_number).exists():
            raise forms.ValidationError("This national number is already registered.")
        return national_number

    def clean_full_name(self):
        return (self.cleaned_data.get("full_name") or "").strip()

    def clean_phone_number(self):
        return (self.cleaned_data.get("phone_number") or "").strip()

    def clean_address(self):
        return (self.cleaned_data.get("address") or "").strip()

    def clean_post_id(self):
        return (self.cleaned_data.get("post_id") or "").strip()
