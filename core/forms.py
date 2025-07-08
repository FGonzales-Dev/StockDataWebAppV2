from django import forms

class getDataForm():
    class Meta:
        fields = ["ticker", "market"]

class EmailSubscriptionForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control',
            'required': True
        })
    )