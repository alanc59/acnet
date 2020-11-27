# Generated by Django 2.2.12 on 2020-11-23 23:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Backup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pi', models.CharField(max_length=5)),
                ('date', models.DateField()),
                ('result', models.CharField(choices=[('S', 'Success'), ('F', 'Fail')], default='S', help_text='Method used to show backup result', max_length=1)),
            ],
            options={
                'ordering': ['pi', 'date'],
            },
        ),
    ]
