from django import forms
from .models import Leave,Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service', 'date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['startdate', 'enddate', 'leavetype', 'reason']
        widgets = {
            'startdate': forms.TextInput(attrs={'type': 'date'}),
            'enddate': forms.TextInput(attrs={'type': 'date'}),
        }
