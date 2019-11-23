from django import forms
from django_countries.fields import CountryField


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'Paypal'),
)

class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': "1234 Main Street"
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': "1234 Main Street"
    }))
    country = CountryField(blank_label='(select country)').formfield(attrs={
        'class': "custom-select d-block w-100"
    })
    zipp = forms.CharField(widget=forms.TextInput(attrs={'type':'number'}))
    same_billing_address = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    save_info = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placehodler': 'Promo Code',
        'aria-label': "Recipient\'s username" ,
        'aria-describedby': "basic-addon2"
    }))

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()
