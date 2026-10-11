from django import forms
from django.utils import timezone

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["guest_name", "phone", "email", "check_in", "check_out", "guests", "note"]
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "例如预计到店时间"}),
        }

    def clean_check_in(self):
        check_in = self.cleaned_data["check_in"]
        if check_in < timezone.localdate():
            raise forms.ValidationError("入住日期不能早于今天。")
        return check_in
