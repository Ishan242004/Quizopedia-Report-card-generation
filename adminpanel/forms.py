from django import forms
from user.models import Question

class QuestionForm(forms.Form):
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition',
            'placeholder': 'e.g. Mathematics, Python, Python Functions, etc.',
        }),
        error_messages={
            'required': 'Subject is required.',
        }
    )
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] placeholder:text-[var(--input-placeholder)] focus:border-[var(--accent-primary)]/50 transition h-48 resize-y',
            'placeholder': "Format 1 – Simple Q&A (sirf question aur answer):\n\nQ1. Python mein OOP ka full form kya hai?\nCorrect Answer: Object Oriented Programming\n\nQ2. Python mein class banane ke liye keyword?\nCorrect Answer: class\n\n---\nFormat 2 – MCQ (A/B/C/D options ke saath):\n\nQ1. Python mein OOP ka full form kya hai?\nA) Object Oriented Programming\nB) Object Ordered Programming\nC) Oriented Object Programming\nD) Object Operating Program\nCorrect Answer: A",
        }),
        required=True,
        error_messages={
            'required': 'Question text is required.',
        }
    )


class QuestionEditForm(forms.ModelForm):
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition',
            'placeholder': 'e.g. Mathematics, Python, Python Functions, etc.',
        }),
        error_messages={
            'required': 'Subject is required.',
        }
    )

    class Meta:
        model = Question
        fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] placeholder:text-[var(--input-placeholder)] focus:border-[var(--accent-primary)]/50 transition h-24 resize-y',
                'placeholder': 'Enter the question here...',
            }),
            'option_a': forms.TextInput(attrs={
                'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition',
                'placeholder': 'Enter Option A',
            }),
            'option_b': forms.TextInput(attrs={
                'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition',
                'placeholder': 'Enter Option B',
            }),
            'option_c': forms.TextInput(attrs={
                'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition',
                'placeholder': 'Enter Option C',
            }),
            'option_d': forms.TextInput(attrs={
                'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition',
                'placeholder': 'Enter Option D',
            }),
            'correct_option': forms.Select(attrs={
                'class': 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition bg-slate-900',
            }),
        }
        error_messages = {
            'question_text': {'required': 'Question text is required.'},
            'option_a': {'required': 'Option A is required.'},
            'option_b': {'required': 'Option B is required.'},
            'option_c': {'required': 'Option C is required.'},
            'option_d': {'required': 'Option D is required.'},
            'correct_option': {'required': 'Correct option is required.'},
        }
