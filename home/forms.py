from django import forms 
from .models import home

class homeForm(forms.ModelForm):
    class Meta:
        model = home
        fields =['text','photo']
