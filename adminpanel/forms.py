from django import forms

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
            'placeholder': "Enter question here...\nIf adding multiple questions, paste them with each question on a new line.",
        }),
        required=True,
        error_messages={
            'required': 'Question text is required.',
        }
    )
