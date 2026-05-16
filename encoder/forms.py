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


class EncodingProfileForm(forms.ModelForm):
    class Meta:
        model = EncodingProfile
        fields = [
            "name", "mode", "video_codec", "quality_crf", "encoder_preset",
            "resolution", "audio_mode", "container", "subtitle_default_lang",
            "burn_forced_subs", "soft_subs", "skip_existing",
            "keep_folder_structure", "delete_source",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "quality_crf": forms.NumberInput(attrs={"class": "w-20 p-2 border rounded", "min": 0, "max": 51}),
            "encoder_preset": forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
            "container": forms.TextInput(attrs={"class": "w-20 p-2 border rounded"}),
            "subtitle_default_lang": forms.TextInput(attrs={"class": "w-20 p-2 border rounded"}),
        }
