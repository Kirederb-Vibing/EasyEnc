from django import forms

from .models import EncodingProfile


class ScanForm(forms.Form):
    MODE_CHOICES = [("film", "Film"), ("serie", "Serie")]

    source_path = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            "class": "w-full p-2 border rounded",
            "placeholder": "/media/source",
        }),
    )
    output_path = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            "class": "w-full p-2 border rounded",
            "placeholder": "/media/output",
        }),
    )
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
    )
    profile = forms.ModelChoiceField(
        queryset=EncodingProfile.objects.all(),
        required=False,
        empty_label="-- Vælg profil --",
        widget=forms.Select(attrs={"class": "w-full p-2 border rounded"}),
    )
