# Generated manually for Django 6.1

import django.db.models.functions.text
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_studentotp'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ['name'], 'verbose_name': 'Subject', 'verbose_name_plural': 'Subjects'},
        ),
        migrations.AddField(
            model_name='subject',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created At'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subject',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='description',
            field=models.TextField(blank=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=150, unique=True, verbose_name='Subject Name'),
        ),
        migrations.AddConstraint(
            model_name='subject',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('name'), name='unique_subject_name_case_insensitive'),
        ),
    ]
