from django.db import models
from django import forms
from django.urls import reverse
from django.conf import settings
from django.forms.models import model_to_dict


GLOBAL_TARGET_FIELDS = ['identifier', 'name', 'designation', 'type']

SIDEREAL_FIELDS = GLOBAL_TARGET_FIELDS + [
    'ra', 'dec', 'epoch', 'pm_ra', 'pm_dec',
    'galactic_lng', 'galactic_lat', 'distance', 'distance_err'
]

NON_SIDEREAL_FIELDS = GLOBAL_TARGET_FIELDS + [
    'mean_anomaly', 'arg_of_perihelion',
    'lng_asc_node', 'inclination', 'mean_daily_motion', 'semimajor_axis',
    'ephemeris_period', 'ephemeris_period_err', 'ephemeris_epoch',
    'ephemeris_epoch_err'
]


class Target(models.Model):
    SIDEREAL = 'SIDEREAL'
    NON_SIDEREAL = 'NON_SIDEREAL'
    TARGET_TYPES = ((SIDEREAL, 'Sidereal'), (NON_SIDEREAL, 'Non-sidereal'))

    identifier = models.CharField(max_length=100, verbose_name='Identifier', help_text='The identifier for this object, e.g. Kelt-16b.')
    name = models.CharField(max_length=100, default='', verbose_name='Name', help_text='The name of this target e.g. Barnard\'s star.')
    type = models.CharField(max_length=100, choices=TARGET_TYPES, verbose_name='Target Type', help_text='The type of this target.')
    designation = models.CharField(max_length=100, default='', verbose_name='Designation', help_text='Designation of this target.')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Time Created', help_text='The time which this target was created in the TOM database.')
    modified = models.DateTimeField(auto_now=True, verbose_name='Last Modified', help_text='The time which this target was changed in the TOM database.')
    ra = models.FloatField(null=True, blank=True, verbose_name='Right Ascension', help_text='Right Ascension, in degrees.')
    dec = models.FloatField(null=True, blank=True, verbose_name='Declination', help_text='Declination, in degrees.')
    epoch = models.FloatField(null=True, blank=True, verbose_name='Epoch of Elements', help_text='Julian Years. Max 2100.')
    pm_ra = models.FloatField(null=True, blank=True, verbose_name='Proper Motion (RA)', help_text='Proper Motion: RA. Milliarsec/year.')
    pm_dec = models.FloatField(null=True, blank=True, verbose_name='Proper Motion (Declination)', help_text='Proper Motion: Dec. Milliarsec/year.')
    galactic_lng = models.FloatField(null=True, blank=True, verbose_name='Galactic Longitude', help_text='Galactic Longitude in degrees.')
    galactic_lat = models.FloatField(null=True, blank=True, verbose_name='Galactic Latitude', help_text='Galactic Latitude in degrees.')
    distance = models.FloatField(null=True, blank=True, verbose_name='Distance', help_text='Parsecs.')
    distance_err = models.FloatField(null=True, blank=True, verbose_name='Distance Error', help_text='Parsecs.')
    mean_anomaly = models.FloatField(null=True, blank=True, verbose_name='Mean Anomaly', help_text='Angle in degrees.')
    arg_of_perihelion = models.FloatField(null=True, blank=True, verbose_name='Argument of Perihelion', help_text='Argument of Perhihelion. J2000. Degrees.')
    lng_asc_node = models.FloatField(null=True, blank=True, verbose_name='Longitude of Ascending Node', help_text='Longitude of Ascending Node. J2000. Degrees.')
    inclination = models.FloatField(null=True, blank=True, verbose_name='Inclination to the ecliptic', help_text='Inclination to the ecliptic. J2000. Degrees.')
    mean_daily_motion = models.FloatField(null=True, blank=True, verbose_name='Mean Daily Motion', help_text='Degrees per day.')
    semimajor_axis = models.FloatField(null=True, blank=True, verbose_name='Semimajor Axis', help_text='In AU')
    ephemeris_period = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Period', help_text='Days')
    ephemeris_period_err = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Period Error', help_text='Days')
    ephemeris_epoch = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Epoch', help_text='Days')
    ephemeris_epoch_err = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Epoch Error', help_text='Days')

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.identifier

    def get_absolute_url(self):
        return reverse('targets:detail', kwargs={'pk': self.id})

    def as_dict(self):
        if self.type == self.SIDEREAL:
            fields_for_type = SIDEREAL_FIELDS
        elif self.type == self.NON_SIDEREAL:
            fields_for_type = NON_SIDEREAL_FIELDS
        else:
            fields_for_type = GLOBAL_TARGET_FIELDS

        return model_to_dict(self, fields=fields_for_type)


class TargetList(models.Model):
    name = models.CharField(max_length=200, help_text='The name of the target list.')
    targets = models.ManyToManyField(Target)
    created = models.DateTimeField(auto_now_add=True, help_text='The time which this target list was created in the TOM database.')

    def __str__(self):
        return self.name