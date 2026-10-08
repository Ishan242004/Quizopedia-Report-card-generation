from django.core.management.base import BaseCommand
from user.models import Subject, Question, Option


class Command(BaseCommand):
    help = (
        "Populate sample quiz data for Report Card Generation: "
        "3 Subjects, 6 Questions total (2 per subject), 4 Options per question (1 correct answer)."
    )

    SAMPLE_DATA = [
        {
            'name': 'Python Programming',
            'description': 'Fundamentals of Python programming including data types, functions, and control structures.',
            'questions': [
                {
                    'topic': 'Python data types',
                    'question_text': 'Which of the following data types in Python is immutable?',
                    'option_a': 'Tuple',
                    'option_b': 'List',
                    'option_c': 'Dictionary',
                    'option_d': 'Set',
                    'correct_option': 'A',
                },
                {
                    'topic': 'Python functions',
                    'question_text': 'Which keyword is used to define a function in Python?',
                    'option_a': 'function',
                    'option_b': 'def',
                    'option_c': 'fun',
                    'option_d': 'define',
                    'correct_option': 'B',
                },
            ],
        },
        {
            'name': 'Mathematics',
            'description': 'Core mathematical concepts covering basic algebra, percentages, and arithmetic operations.',
            'questions': [
                {
                    'topic': 'Basic algebra',
                    'question_text': 'Solve for x: If 2x + 5 = 15, what is the value of x?',
                    'option_a': '3',
                    'option_b': '4',
                    'option_c': '5',
                    'option_d': '10',
                    'correct_option': 'C',
                },
                {
                    'topic': 'Percentage',
                    'question_text': 'What is 25% of 200?',
                    'option_a': '50',
                    'option_b': '25',
                    'option_c': '75',
                    'option_d': '100',
                    'correct_option': 'A',
                },
            ],
        },
        {
            'name': 'Computer Science',
            'description': 'Foundational computer science topics including operating systems, networking, and hardware.',
            'questions': [
                {
                    'topic': 'Operating systems',
                    'question_text': 'Which component of an operating system is responsible for managing CPU scheduling and memory?',
                    'option_a': 'Kernel',
                    'option_b': 'Shell',
                    'option_c': 'File System',
                    'option_d': 'Compiler',
                    'correct_option': 'A',
                },
                {
                    'topic': 'Computer networks',
                    'question_text': 'Which protocol is primarily used for securely transferring web pages over the Internet?',
                    'option_a': 'FTP',
                    'option_b': 'HTTP',
                    'option_c': 'SMTP',
                    'option_d': 'HTTPS',
                    'correct_option': 'D',
                },
            ],
        },
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Populating Quizopedia sample data..."))

        created_subjects_count = 0
        created_questions_count = 0

        for subj_data in self.SAMPLE_DATA:
            subject, s_created = Subject.objects.get_or_create(
                name=subj_data['name'],
                defaults={'description': subj_data['description']}
            )
            if s_created:
                created_subjects_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [+] Created Subject: '{subject.name}'"))
            else:
                self.stdout.write(f"  [*] Subject already exists: '{subject.name}'")

            for q_data in subj_data['questions']:
                question = Question.objects.filter(
                    subject=subject,
                    question_text=q_data['question_text']
                ).first()

                if not question:
                    question = Question.objects.create(
                        subject=subject,
                        question_type='mcq',
                        question_text=q_data['question_text'],
                        option_a=q_data['option_a'],
                        option_b=q_data['option_b'],
                        option_c=q_data['option_c'],
                        option_d=q_data['option_d'],
                        correct_option=q_data['correct_option'],
                    )
                    created_questions_count += 1
                    self.stdout.write(self.style.SUCCESS(f"    [+] Created Question: {question.question_text} (Topic: {q_data['topic']})"))
                else:
                    # Update fields to ensure synchronization
                    question.question_type = 'mcq'
                    question.option_a = q_data['option_a']
                    question.option_b = q_data['option_b']
                    question.option_c = q_data['option_c']
                    question.option_d = q_data['option_d']
                    question.correct_option = q_data['correct_option']
                    question.save()
                    self.stdout.write(f"    [*] Synchronized Question: {question.question_text}")

                # Guarantee that Option records are synced with legacy fields
                question.sync_options()

        self.stdout.write(self.style.MIGRATE_HEADING("\nVerification:"))
        sample_subject_names = [s['name'] for s in self.SAMPLE_DATA]
        subjects = Subject.objects.filter(name__in=sample_subject_names)
        self.stdout.write(f"  Sample Subjects count: {subjects.count()}")

        total_questions = 0
        total_options = 0

        for subj in subjects:
            q_list = Question.objects.filter(subject=subj)
            self.stdout.write(f"  Subject: '{subj.name}' -> {q_list.count()} questions")
            total_questions += q_list.count()

            for q in q_list:
                opts = Option.objects.filter(question=q).order_by('id')
                total_options += opts.count()
                correct_opts = opts.filter(is_answer=True)
                self.stdout.write(
                    f"    - Q: '{q.question_text[:40]}...' | Options: {opts.count()} | Correct: {correct_opts.count()} ({q.correct_option}: {q.correct_answer_text})"
                )
                assert opts.count() == 4, f"Question {q.id} does not have exactly 4 options!"
                assert correct_opts.count() == 1, f"Question {q.id} does not have exactly 1 correct answer!"

        self.stdout.write(self.style.SUCCESS(
            f"\nCompleted successfully! Total Sample Subjects: {subjects.count()}, Total Questions: {total_questions}, Total Options: {total_options}"
        ))
