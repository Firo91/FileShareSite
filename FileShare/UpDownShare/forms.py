from django import forms
from .models import CustomUser, Folder
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    folder = forms.ModelChoiceField(queryset=Folder.objects.all(), required=False)
    
class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
    
class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username','name', 'country', 'password1', 'password2')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.country = self.cleaned_data['country']
        if commit:
            user.save()
        return user
    
class CustomPasswordResetForm(forms.Form):
    username = forms.CharField(max_length=150)
    name = forms.CharField(max_length=150)

class FolderUserRelationshipForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(FolderUserRelationshipForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = CustomUser.objects.exclude(username=user.username)
    
    user = forms.ModelChoiceField(queryset=CustomUser.objects.none())