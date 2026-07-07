from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 5, 'type': 'number',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Share your thoughts about this product...',
            }),
        }
