from django import forms
from .models import Vendor

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['nama_vendor']  # Pilih field yang ingin ditampilkan di form

        labels = {
            'nama_vendor': 'Suplier Name',
            'is_active': 'Active',
        }

        widgets = {
            'nama_vendor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vendor name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        help_texts = {
            # 'nama_vendor': "Enter the vendor's name. It should be between 4 and 100 characters.",
        }