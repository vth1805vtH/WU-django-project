import re

from django import forms

from accounts.models import Address, PaymentMethod


VISA_SLUG = 'visa-card'


class CheckoutForm(forms.Form):
    address_id = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        widget=forms.RadioSelect,
    )
    payment_method_id = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        widget=forms.RadioSelect,
    )
    full_name = forms.CharField(max_length=255, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    address_line_1 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=100, required=False)
    province_or_state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    country = forms.CharField(max_length=100, required=False)
    save_address = forms.BooleanField(required=False, initial=True)
    cardholder_name = forms.CharField(max_length=255, required=False)
    card_number = forms.CharField(max_length=19, required=False)
    expiry_date = forms.CharField(max_length=5, required=False)
    cvv = forms.CharField(max_length=4, required=False)
    confirm = forms.BooleanField(
        required=True,
        error_messages={'required': 'Please confirm your order.'},
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['address_id'].queryset = Address.objects.filter(user=user)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput)):
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css} form-check-input'.strip()

    def _is_visa(self, cleaned_data):
        pm = cleaned_data.get('payment_method_id')
        return pm is not None and pm.slug == VISA_SLUG

    def clean(self):
        cleaned_data = super().clean()
        address_id = cleaned_data.get('address_id')

        if not address_id:
            required = ['full_name', 'phone_number', 'address_line_1',
                        'city', 'province_or_state', 'postal_code', 'country']
            for field_name in required:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, 'This field is required.')

        if not cleaned_data.get('payment_method_id'):
            self.add_error('payment_method_id', 'Please select a payment method.')

        if self._is_visa(cleaned_data):
            card_fields = {
                'cardholder_name': 'Cardholder name',
                'card_number': 'Card number',
                'expiry_date': 'Expiry date',
                'cvv': 'CVV',
            }
            for field, label in card_fields.items():
                if not cleaned_data.get(field):
                    self.add_error(field, f'{label} is required.')

            card_number = cleaned_data.get('card_number', '')
            if card_number and not re.fullmatch(r'\d{13,19}', card_number.replace(' ', '')):
                self.add_error('card_number', 'Enter a valid card number.')

            expiry = cleaned_data.get('expiry_date', '')
            if expiry and not re.fullmatch(r'(0[1-9]|1[0-2])/\d{2}', expiry):
                self.add_error('expiry_date', 'Use MM/YY format.')

            cvv = cleaned_data.get('cvv', '')
            if cvv and not re.fullmatch(r'\d{3,4}', cvv):
                self.add_error('cvv', 'Enter a valid CVV.')

        return cleaned_data
