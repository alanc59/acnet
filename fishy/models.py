from django.db import models
from django.urls import reverse

# Create your models here.

class Fish(models.Model):
    name = models.CharField(max_length=20)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'

    def __unicode__(self):
        return self.name

class Venue(models.Model):
    name = models.CharField(max_length=25)
	
    YES_OR_NO = (('Y', 'Yes'), ('N', 'No'))

    wac = models.CharField(max_length=1, choices=YES_OR_NO, help_text='Withnell Water or not')
 
    postcode = models.CharField(max_length=10, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this venue."""
        return reverse('venue-detail', args=[str(self.id)])

class Bait(models.Model):
    name = models.CharField(max_length=20)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'

class Trip(models.Model):
    date = models.DateField()
    venue = models.ForeignKey('Venue', on_delete=models.SET_NULL, null=True)
   
    class Meta:
        ordering = ['-date', 'venue']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.date}, {self.venue}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this trip."""
        return reverse('trip-detail', args=[str(self.id)])

class Catch(models.Model):
    fish = models.ForeignKey('Fish', on_delete=models.SET_NULL, null=True)
    weight = models.IntegerField(help_text='Weight in ounces')
    YES_OR_NO = (('Y', 'Yes'), ('N', 'No'))
    weighed = models.CharField(max_length=1, choices=YES_OR_NO, default='Y', help_text='Weighed (if N = estimated)')
    trip = models.ForeignKey('Trip', on_delete=models.SET_NULL, null=True)
    bait = models.ForeignKey('Bait', on_delete=models.SET_NULL, null=True)
    METHOD = (('F', 'Float'), ('L', 'Ledger'))
    method = models.CharField(max_length=1, choices=METHOD, default='F', help_text='Method used for catch')
    
    class Meta:
        ordering = ['trip', 'fish', '-weight']
    
    def __str__(self):
        """String for representing the Model object."""
        return f'{self.trip}, {self.fish}, Weight (oz)={self.weight}, Weighed={self.weighed}, {self.bait}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this catch."""
        return reverse('catch-detail', args=[str(self.id)])
