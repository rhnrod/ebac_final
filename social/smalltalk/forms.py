from django import forms
from .models import Post, User

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
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