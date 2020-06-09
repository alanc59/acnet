from django.db import models

# Create your models here.

class Backup(models.Model):
    pi = models.CharField(max_length=5)
    date = models.DateField()
    RESULT = (('S', 'Success'), ('F', 'Fail'))
    result = models.CharField(max_length=1, choices=RESULT, default='S', help_text='Method used to show backup result')

    class Meta:
        ordering = ['pi', 'date']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.pi} - {self.date} : {self.result}'

