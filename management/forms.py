from django import forms
from .models import Key, School
from .key_generator import generate_access_key


class AccessKeyForm(forms.ModelForm):
    class Meta:
        model=Key
        fields=('expiry_date',)

    def generate_access_key(self):
        return generate_access_key

    def save(self, commit=True):
        access_key = super().save(commit=False)
        access_key.expiry_date = self.cleaned_data.get('expiry_date')
        access_key.key = self.generate_access_key()
        if commit:
            access_key.save()
        return access_key 


class SchoolForm(forms.ModelForm):
    name = forms.CharField()
    
    class Meta:
        model=School
        fields=('name',) 



class MailForm(forms.Form):
    email = forms.EmailField(max_length=200, required=True)


