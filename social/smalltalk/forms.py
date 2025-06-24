from django import forms
from .models import Post, Profile

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ['likes']
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'id': 'post-input',
                'maxlength': 255,
                'class': 'w-full bg-transparent resize-none outline-none border-none',
                'rows': 4,
                'placeholder': 'Compartilhe uma ideia...',
            }),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['description', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={
                'id': 'bio-input',
                'maxlength': 80,
                'class': 'textarea w-full h-auto resize-none bg-transparent text-white border outline-0 border-zinc-500',
                'rows': 2,
                'placeholder': 'Bio',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'id': 'is-public',
                'class': 'checkbox checkbox-warning checkbox-sm',
            }),
        }

class ProfilePicForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic', 'cover_pic']
        widgets = {
            'profile_pic': forms.FileInput(attrs={
                'id': 'profile-pic-input',
                'class': 'file-input outline-none bg-zinc-800 text-white border-zinc-600 placeholder-gray-400',
                'accept': '.png, .jpg, .jpeg',
            }),
            'cover_pic': forms.FileInput(attrs={
                'id': 'cover-pic-input',
                'class': 'file-input outline-none bg-zinc-800 text-white border-zinc-600 placeholder-gray-400',
                'accept': '.png, .jpg, .jpeg',
            }),
        }

class SearchForm(forms.Form):
    query = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={
        'id': 'search-input',
        'type': 'search',
        'maxlength': 255,
        'name': 'search',
        'class': 'grow bg-none outline-0 border-0 text-white',
        'placeholder': 'Pesquisar...',
        'oninput': 'toggleClearButton()',
    }))