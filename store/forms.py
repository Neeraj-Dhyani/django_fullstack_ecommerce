from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Order


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "phone", "address", "city", "pincode", "payment_method"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if not phone.lstrip("+").isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_pincode(self):
        pin = self.cleaned_data["pincode"].strip()
        if not (pin.isdigit() and len(pin) == 6):
            raise forms.ValidationError("Enter a 6-digit pincode.")
        return pin
