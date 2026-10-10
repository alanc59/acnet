from django.conf import settings
from django.db import models
from django.urls import reverse
from util.utilities import *
from django.utils import timezone   # after the * import so nothing in utilities can replace it


def angler_name(user):
    """How an angler's name is shown: full name if set, otherwise username."""
    if user is None:
        return ''
    return user.get_full_name() or user.get_username()


class Fish(models.Model):
    name = models.CharField(max_length=20)
    latin_name = models.CharField(max_length=35, null=True)
    uk_record = models.IntegerField(help_text='Weight in ounces')

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a detail record for this fish."""
        return reverse('fish-detail', args=[str(self.id)])

class Venue(models.Model):
    name = models.CharField(max_length=25)

    YES_OR_NO = (('Y', 'Yes'), ('N', 'No'))

    wac = models.CharField(max_length=1, choices=YES_OR_NO, help_text='Withnell Water or not')

    postcode = models.CharField(max_length=10, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='venues')   # owner (angler)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this venue."""
        return reverse('venue-detail', args=[str(self.id)])

    @property
    def angler(self):
        """Owner's display name."""
        return angler_name(self.user)


class Bait(models.Model):
    name = models.CharField(max_length=20)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='baits')   # owner (angler)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this trip."""
        return reverse('bait-detail', args=[str(self.id)])

    @property
    def angler(self):
        """Owner's display name."""
        return angler_name(self.user)


class Trip(models.Model):
    date = models.DateField()
    venue = models.ForeignKey('Venue', on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='trips')   # owner (angler)

    class Meta:
        ordering = ['-date', 'venue']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.date}, {self.venue}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this trip."""
        return reverse('trip-detail', args=[str(self.id)])

    @property
    def total_weight_display(self):
        if self.total_weight is None:
            return "0-00"

        lbs = self.total_weight // 16
        oz = self.total_weight % 16
        return f"{lbs} lbs -{oz:02d} oz"

    @property
    def angler(self):
        """Owner's display name."""
        return angler_name(self.user)


class Catch(models.Model):
    fish = models.ForeignKey('Fish', on_delete=models.SET_NULL, null=True)
    weight = models.IntegerField(help_text='Weight in ounces')
    YES_OR_NO = (('Y', 'Yes'), ('N', 'No'))
    weighed = models.CharField(max_length=1, choices=YES_OR_NO, default='Y', help_text='Weighed (if N = estimated)')
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE, null=True)   # deleting a trip deletes its catches
    bait = models.ForeignKey('Bait', on_delete=models.SET_NULL, null=True)
    METHOD = (('F', 'Float'), ('L', 'Ledger'), ('M', 'Method Feeder'))
    method = models.CharField(max_length=1, choices=METHOD, default='F', help_text='Method used for catch')
    catch_time = models.DateTimeField(default=timezone.now)
    photo =  models.CharField(max_length=1, choices=YES_OR_NO, default='N')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='catches')   # owner (angler)

    class Meta:
        #ordering = ['trip', '-catch_time', '-weight', 'fish']
        ordering = ['-trip__date', '-catch_time']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.trip}, {self.fish}, Weight (oz)={self.weight}, Weighed={self.weighed}, {self.bait}, {self.catch_time}, {self.photo}'

    def get_absolute_url(self):
        """Returns the url to access a detail record for this catch."""
        return reverse('catch-detail', args=[str(self.id)])

    @property
    def weight_display(self):
        return toPoundsAndOunces(self.weight)

    @property
    def angler(self):
        """Owner's display name."""
        return angler_name(self.user)
