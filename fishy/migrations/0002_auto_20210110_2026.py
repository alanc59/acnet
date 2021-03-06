# Generated by Django 3.1.4 on 2021-01-10 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fishy', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fish',
            name='latin_name',
            field=models.CharField(max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='fish',
            name='uk_record',
            field=models.IntegerField(default=0, help_text='Weight in ounces'),
            preserve_default=False,
        ),
    ]
