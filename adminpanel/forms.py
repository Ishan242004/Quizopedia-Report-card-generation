from django import forms
from user.models import Question

# Shared widget CSS classes
INPUT_CLASS = 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition'
TEXTAREA_CLASS = 'w-full px-4 py-3 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] placeholder:text-[var(--input-placeholder)] focus:border-[var(--accent-primary)]/50 transition resize-y'
SELECT_CLASS = 'w-full h-11 px-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-sm outline-none text-[var(--input-text)] focus:border-[var(--accent-primary)]/50 transition'


# =============================================================================
# EXISTING FORMS (preserved for backward compatibility)
# =============================================================================

class QuestionForm(forms.Form):
    """Original bulk add form — kept for backward compatibility."""
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Mathematics, Python, Python Functions, etc.',
        }),
        error_messages={
            'required': 'Subject is required.',
        }
    )
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': f'{TEXTAREA_CLASS} h-48',
            'placeholder': "Format 1 – Simple Q&A (sirf question aur answer):\n\nQ1. Python mein OOP ka full form kya hai?\nCorrect Answer: Object Oriented Programming\n\nQ2. Python mein class banane ke liye keyword?\nCorrect Answer: class\n\n---\nFormat 2 – MCQ (A/B/C/D options ke saath):\n\nQ1. Python mein OOP ka full form kya hai?\nA) Object Oriented Programming\nB) Object Ordered Programming\nC) Oriented Object Programming\nD) Object Operating Program\nCorrect Answer: A",
        }),
        required=True,
        error_messages={
            'required': 'Question text is required.',
        }
    )


class QuestionEditForm(forms.ModelForm):
    """Original edit form — kept for backward compatibility."""
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
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
                'class': f'{TEXTAREA_CLASS} h-24',
                'placeholder': 'Enter the question here...',
            }),
            'option_a': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option A',
            }),
            'option_b': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option B',
            }),
            'option_c': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option C',
            }),
            'option_d': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option D',
            }),
            'correct_option': forms.Select(attrs={
                'class': SELECT_CLASS,
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


# =============================================================================
# NEW FORMS — Question & Answer
# =============================================================================

class QnAAddForm(forms.Form):
    """Simple & Bulk Q&A add form: Subject + Question textarea with bulk format support."""
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Mathematics, Python, Django, etc.',
        }),
        error_messages={
            'required': 'Subject is required.',
        }
    )
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': f'{TEXTAREA_CLASS} h-80',
            'placeholder': "Format 1 – Simple Q&A (sirf question aur answer):\n\nQ1. Python mein OOP ka full form kya hai?\nCorrect Answer: Object Oriented Programming\n\nQ2. Python mein class banane ke liye keyword?\nCorrect Answer: class\n\n---",
            'id': 'qna-textarea',
        }),
        required=True,
        error_messages={
            'required': 'Question text is required.',
        }
    )
    answer = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter the correct answer...',
        }),
    )


class QnAEditForm(forms.Form):
    """Edit form for Q&A questions: Subject + Question + Answer."""
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Mathematics, Python, Django, etc.',
        }),
        error_messages={
            'required': 'Subject is required.',
        }
    )
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': f'{TEXTAREA_CLASS} h-24',
            'placeholder': 'Enter your question here...',
        }),
        required=True,
        error_messages={
            'required': 'Question text is required.',
        }
    )
    answer = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter the correct answer...',
        }),
        error_messages={
            'required': 'Answer is required.',
        }
    )


# =============================================================================
# NEW FORMS — 4 Option MCQ
# =============================================================================

class MCQBulkForm(forms.Form):
    """MCQ bulk import form: Subject + textarea for pasting multiple MCQs."""
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Mathematics, Python, Django, etc.',
        }),
        error_messages={
            'required': 'Subject is required.',
        }
    )
    mcq_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': f'{TEXTAREA_CLASS} h-80',
            'placeholder': 'Paste your MCQ questions in this format:\n\nQ1. Python mein OOP ka full form kya hai?\nA) Object Oriented Programming\nB) Online Object Programming\nC) Object Order Programming\nD) None of the Above\nCorrect Answer: A\n\nQ2. Python mein class banane ke liye kaunsa keyword use hota hai?\nA) function\nB) class\nC) object\nD) define\nCorrect Answer: B\n\nQ3. Python mein list ka symbol kya hai?\nA) {}\nB) ()\nC) []\nD) <>\nCorrect Answer: C',
            'id': 'mcq-textarea',
        }),
        required=True,
        error_messages={
            'required': 'Please paste your MCQ questions.',
        }
    )


class MCQEditForm(forms.ModelForm):
    """Edit form for MCQ questions: all 4 options + correct answer dropdown."""
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Mathematics, Python, Django, etc.',
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
                'class': f'{TEXTAREA_CLASS} h-24',
                'placeholder': 'Enter the question here...',
            }),
            'option_a': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option A',
            }),
            'option_b': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option B',
            }),
            'option_c': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option C',
            }),
            'option_d': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter Option D',
            }),
            'correct_option': forms.Select(attrs={
                'class': SELECT_CLASS,
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
