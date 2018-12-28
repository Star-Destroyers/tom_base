import requests
from django.conf import settings
from django import forms
from dateutil.parser import parse
from crispy_forms.layout import Layout, Div
# from django.core.cache import cache
# from datetime import datetime

from tom_observations.facility import GenericObservationForm
from tom_common.exceptions import ImproperCredentialsException
from tom_observations.facility import GenericObservationFacility
from tom_targets.models import Target

from gsselect import gsselect
from parangle import parangle

try:
    GEM_SETTINGS = settings.FACILITIES['GEM']
except AttributeError:
    GEM_SETTINGS = {
        # 'portal_url': 'https://139.229.34.15:8443',
        'portal_url': 'https://gsodbtest.gemini.edu:8443',
        'api_key': '',
    }

PORTAL_URL = GEM_SETTINGS['portal_url']
TERMINAL_OBSERVING_STATES = ['TRIGGERED', 'ON_HOLD']
SITES = {
    'Cerro Pachon': {
        'sitecode': 'cpo',
        'latitude': -30.24075,
        'longitude': -70.736694,
        'elevation': 2722.
    },
    'Maunakea': {
        'sitecode': 'mko',
        'latitude': 19.8238,
        'longitude': -155.46905,
        'elevation': 4213.
    }
}


def make_request(*args, **kwargs):
    response = requests.request(*args, **kwargs)
    if 400 <= response.status_code < 500:
        print('Request failed: {}'.format(response.content))
        raise ImproperCredentialsException('GEM')
    response.raise_for_status()
    return response


def flatten_error_dict(form, error_dict):
    non_field_errors = []
    for k, v in error_dict.items():
        if type(v) == list:
            for i in v:
                if type(i) == str:
                    if k in form.fields:
                        form.add_error(k, i)
                    else:
                        non_field_errors.append('{}: {}'.format(k, i))
                if type(i) == dict:
                    non_field_errors.append(flatten_error_dict(form, i))
        elif type(v) == str:
            if k in form.fields:
                form.add_error(k, v)
            else:
                non_field_errors.append('{}: {}'.format(k, v))
        elif type(v) == dict:
            non_field_errors.append(flatten_error_dict(form, v))

    return non_field_errors


# def get_instruments():
#     response = make_request(
#         'GET',
#         PORTAL_URL + '/api/instruments/',
#         headers={'Authorization': 'Token {0}'.format(GEM_SETTINGS['api_key'])}
#     )
#     return response.json()
# 
# 
# def instrument_choices():
#     return [(k, k) for k in get_instruments()]
# 
# 
# def filter_choices():
#     return set([(f, f) for ins in get_instruments().values() for f in ins['filters']])


def proposal_choices():
    choices = []
    for p in GEM_SETTINGS['programs']:
        choices.append((p,p))
    return choices

def obs_choices():
    choices = []
    for p in GEM_SETTINGS['programs']:
        for obs in GEM_SETTINGS['programs'][p]:
            obsid = p + '-' + obs
            val = p.split('-')
            showtext = val[0][1]+val[1][2:]+val[2]+val[3]+ ' - '+ GEM_SETTINGS['programs'][p][obs]
            choices.append((obsid,showtext))
    return choices
    
def get_site(progid,location=False):
    values = progid.split('-')
    gemloc = {'GS':'Gemini South','GN':'Gemini North'}
    site = values[0].upper()
    if location:
        site = gemloc[site]
    return site

class GEMObservationForm(GenericObservationForm):

    # Field for the URL API
    # progid = forms.CharField()
    #progid = forms.ChoiceField(choices=proposal_choices)
    # userkey = forms.CharField(get_site(self.cleaned_data[progid]))
    # email = forms.CharField(choices=GEM_SETTINGS['user_email'])
    # obsnum = forms.IntegerField(min_value=1)
    obsid = forms.ChoiceField(choices=obs_choices())
    ready = forms.ChoiceField(
        choices=(('false', 'No'), ('true', 'Yes'))
    )
    brightness = forms.FloatField(required=False)
    brightness_system =forms.ChoiceField(required=False, initial='AB',
        choices=(('Vega', 'Vega'), ('AB', 'AB'), ('Jy', 'Jy'))
    )
    brightness_band = forms.ChoiceField(required=False, initial='r',
        choices=(('u', 'u'), ('U', 'U'), ('B', 'B'), ('g', 'g'), ('V', 'V'), ('UC', 'UC'), ('r', 'r'), ('R', 'R'),
                 ('i', 'i'), ('I', 'I'), ('z', 'z'), ('Y', 'Y'), ('J', 'J'), ('H', 'H'), ('K', 'K'), ('L', 'L'),
                 ('M', 'M'), ('N', 'N'), ('Q', 'Q'), ('AP', 'AP'))
    )
    posangle = forms.FloatField(min_value=0., max_value=360., required=False, initial=0.0, label='Position Angle')
    # posangle = forms.FloatField(min_value=0., max_value=360.,help_text="Position angle in degrees [0-360]")

    group = forms.CharField(required=False)
    note = forms.CharField(required=False)

    eltype = forms.ChoiceField(required=False, label='Airmass/Hour Angle Constraint',
                                choices=(('none', 'None'), ('airmass', 'Airmass'), ('hourAngle', 'Hour Angle')))
    elmin = forms.FloatField(required=False, min_value=-5.0, max_value=5.0, label='Min Airmass/HA', initial=1.0)
    elmax = forms.FloatField(required=False, min_value=-5.0, max_value=5.0, label='Max Airmass/HA', initial=2.0)

    gstarg = forms.CharField(required=False, label='Guide Star Name')
    gsra = forms.CharField(required=False, label='Guide Star RA')
    gsdec = forms.CharField(required=False, label='Guide Star Dec')
    gsbrightness = forms.FloatField(required=False, label = 'Guide Star Brightness')
    gsbrightness_system =forms.ChoiceField(required=False, initial='Vega',
        choices=(('Vega', 'Vega'), ('AB', 'AB'), ('Jy', 'Jy'))
    )
    gsbrightness_band = forms.ChoiceField(required=False, initial='UC', label='Guide Star Brightness Band',
        choices=(('UP', 'u'), ('U', 'U'), ('B', 'B'), ('GP', 'g'), ('V', 'V'), ('UC', 'UC'), ('RP', 'r'), ('R', 'R'),
                 ('IP', 'i'), ('I', 'I'), ('ZP', 'z'), ('Y', 'Y'), ('J', 'J'), ('H', 'H'), ('K', 'K'), ('L', 'L'),
                 ('M', 'M'), ('N', 'N'), ('Q', 'Q'), ('AP', 'AP'))
    )

    # window_start = forms.DateTimeField(required=False)
    window_start = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'date'}),
                                   label='UT Timing Window Start [Date Time]')
    # window_time = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'time'}))
    window_duration = forms.IntegerField(required=False, min_value=1, label='Timing Window Duration [hr]')

    # Fields needed for running parangle/gsselect
    pamode = forms.ChoiceField(required=False, label='PA Mode',
                               choices=(('flip', 'Flip180'), ('fixed', 'Fixed'), ('find', 'PA for best GS'),
                                        ('parallactic', 'Parallactic Angle'))
                               )
    obsdate = forms.CharField(required=False,widget=forms.TextInput(attrs={'type': 'date'}),
                              label='UT Date Time for Obs (for Parallactic PA Mode)')
    # Eventually select instrument from obsid text?
    inst = forms.ChoiceField(required=False, label='Instrument', initial='GMOS',
                                choices=(('GMOS', 'GMOS'), ('GNIRS', 'GNIRS'), ('NIFS', 'NIFS'), ('NIRIF/6', 'NIRIF/6'),
                                         ('NIRIF/14', 'NIRIF/14'),('NIRIF/32', 'NIRIF/32')))
    gsprobe = forms.ChoiceField(required=False, label='Guide Probe', initial='OIWFS',
                                choices=(('OIWFS', 'OIWFS'), ('PWFS1', 'PWFS1'), ('PWFS2', 'PWFS2')))  # GS probe (PWFS1/PWFS2/OIWFS/AOWFS)
    port = forms.ChoiceField(required=False, label='ISS Port',
                                choices=(('side', 'Side'), ('up', 'Up')))
    ifu = forms.ChoiceField(required=False, label='IFU Mode',
                                choices=(('none', 'None'), ('two', 'Two Slit'), ('red', 'One Slit Red')))
    overwrite = forms.ChoiceField(required=False, label='Overwrite previous query?', initial='False',
        choices=(('False', 'No'), ('True', 'Yes')))
    # chop = forms.ChoiceField(required=False, label='Chopping?', initial='false',
    #     choices=(('false', 'No'), ('true', 'Yes')))
    chop = False   # Chopping (no longer used, should be False)
    l_pad = 7.     # Padding applied to WFS FoV (to account for uncertainties in shape) [arcsec]
    l_rmin = -1.   # Minimum radius for guide star search [arcmin], -1 to use default
    iq = forms.ChoiceField(required=False, label='Image Quality', initial='Any',
                                choices=(('20', '20%-tile'), ('70', '70%-tile'), ('85', '85%-tile'), ('Any', 'Any')))
    cc = forms.ChoiceField(required=False, label='Cloud Cover', initial='Any',
                                choices=(('50', '50%-tile'), ('70', '70%-tile'), ('80', '80%-tile'), ('Any', 'Any')))
    sb = forms.ChoiceField(required=False, label='Surface Brightness', initial='Any',
                                choices=(('20', '20%-tile'), ('50', '50%-tile'), ('80', '80%-tile'), ('Any', 'Any')))

    #     start = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
#     end = forms.CharField(widget=forms.TextInput(attrs={'type': 'date'}))
#     filter = forms.ChoiceField(choices=filter_choices)
#     instrument_name = forms.ChoiceField(choices=instrument_choices)
#     exposure_count = forms.IntegerField(min_value=1)
#     exposure_time = forms.FloatField(min_value=0.1)
#     max_airmass = forms.FloatField()
#     observation_type = forms.ChoiceField(
#         choices=(('NORMAL', 'Normal'), ('TARGET_OF_OPPORTUNITY', 'Rapid Response'))
#     )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            self.common_layout,
            Div(
                Div(
                    'obsid', 'posangle', 'brightness', 'eltype', 'note', 'gstarg', 'gsbrightness',
                    css_class='col'
                ),
                Div(
                    'ready', 'pamode', 'brightness_band', 'elmin', 'window_start', 'gsra', 'gsbrightness_band',
                    css_class='col'
                ),
                Div(
                    'group', 'obsdate', 'brightness_system', 'elmax', 'window_duration', 'gsdec', 'gsbrightness_system',
                    css_class='col'
                ),
                css_class='form-row'
            ),
            Div(
                Div(
                    'inst', 'iq', 'overwrite',
                    css_class='col'
                ),
                Div(
                    'gsprobe', 'cc', 'port',
                    css_class='col'
                ),
                Div(
                    'ifu', 'sb',
                    css_class='col'
                ),
                css_class='form-row'
            )
        )

    def is_valid(self):
        super().is_valid()
        errors = GEMFacility.validate_observation(self.observation_payload)
        if errors:
            self.add_error(None, flatten_error_dict(self, errors))
        return not errors

#     def instrument_to_type(self, instrument_name):
#         if any(x in instrument_name for x in ['FLOYDS', 'NRES']):
#             return 'SPECTRUM'
#         else:
#             return 'EXPOSE'

    @property
    def observation_payload(self):

        def isodatetime(value):
            isostring = parse(value).isoformat()
            ii = isostring.find('T')
            date = isostring[0:ii]
            time = isostring[ii + 1:]
            return date, time

        def findgs():

            gstarg = ''
            gsra = ''
            gsdec = ''
            gsmag = ''
            sgsmag = ''
            gspa = 0.0
            spa = str(gspa).strip()
            l_pa = self.cleaned_data['posangle']

            # Convert RA to hours
            target = Target.objects.get(pk=self.cleaned_data['target_id'])
            ra = target.ra / 15.
            dec = target.dec

            l_site = get_site(self.cleaned_data['obsid'],location=True)
            l_pad = 7.
            l_chop = False
            l_rmin = -1.
            # Parallactic angle?
            l_pamode = self.cleaned_data['pamode']
            if l_pamode == 'parallactic':
                if self.cleaned_data['obsdate'].strip() == '':
                    print('WARNING: Observation date must be set in order to calculate the parallactic angle.')
                    return gstarg, gsra, gsdec, sgsmag, spa
                else:
                    odate, otime = isodatetime(self.cleaned_data['obsdate'])
                    l_pa = parangle(str(ra), str(dec), odate, otime, l_site).value
                    l_pamode = 'flip'  # in case of guide star selection

            # Guide star
            overw = self.cleaned_data['overwrite'] == 'True'
            gstarg, gsra, gsdec, gsmag, gspa = gsselect(target.name, str(ra), str(dec), pa=l_pa, imdir=settings.MEDIA_ROOT,
                site=l_site, pad=l_pad, cat='UCAC4', inst=self.cleaned_data['inst'], ifu=self.cleaned_data['ifu'],
                port=self.cleaned_data['port'],
                wfs=self.cleaned_data['gsprobe'], chopping=l_chop, pamode=l_pamode, rmin = l_rmin,
                iq=self.cleaned_data['iq'], cc=self.cleaned_data['cc'], sb=self.cleaned_data['sb'],
                overwrite=overw, display=False, verbose=False,
                figout=True, figfile='default')

            print(gstarg, gsra, gsdec, gsmag, gspa)
            if gstarg != '':
                sgsmag = str(gsmag).strip() + '/UC/Vega'
            spa = str(gspa).strip()

            return gstarg, gsra, gsdec, sgsmag, spa


        target = Target.objects.get(pk=self.cleaned_data['target_id'])
        spa = str(self.cleaned_data['posangle']).strip()

        ii = self.cleaned_data['obsid'].rfind('-')
        progid = self.cleaned_data['obsid'][0:ii]
        obsnum = self.cleaned_data['obsid'][ii+1:]
        # print(progid, obsnum)
        payload = {
            "prog": progid,
            # "password": self.cleaned_data['userkey'],
            "password": GEM_SETTINGS['api_key'][get_site(self.cleaned_data['obsid'])],
            # "email": self.cleaned_data['email'],
            "email": GEM_SETTINGS['user_email'],
            "obsnum": obsnum,
            "target": target.name,
            "ra": target.ra,
            "dec": target.dec,
            "note": self.cleaned_data['note'],
            "ready": self.cleaned_data['ready']
        }

        if self.cleaned_data['brightness'] != None:
            smags = str(self.cleaned_data['brightness']).strip() + '/' + \
                self.cleaned_data['brightness_band'] + '/' + \
                self.cleaned_data['brightness_system']
            payload["mags"] = smags

        if self.cleaned_data['group'].strip() != '':
            payload['group'] = self.cleaned_data['group'].strip()

        # timing window?
        if self.cleaned_data['window_start'].strip() != '':
            wdate, wtime = isodatetime(self.cleaned_data['window_start'])
            payload['windowDate'] = wdate
            payload['windowTime'] = wtime
            payload['windowDuration'] = str(self.cleaned_data['window_duration']).strip()
            # print(payload['windowDate'], payload['windowTime'])

        # elevation/airmass
        if self.cleaned_data['eltype'] != None:
            payload['elevationType'] = self.cleaned_data['eltype']
            payload['elevationMin'] = str(self.cleaned_data['elmin']).strip()
            payload['elevationMax'] = str(self.cleaned_data['elmax']).strip()

        # Guide star
        gstarg = self.cleaned_data['gstarg']
        if gstarg != '':
            gsra = self.cleaned_data['gsra']
            gsdec = self.cleaned_data['gsdec']
            if self.cleaned_data['gsbrightness'] != None:
                sgsmag = str(self.cleaned_data['gsbrightness']).strip() + '/' + \
                     self.cleaned_data['gsbrightness_band'] + '/' + \
                     self.cleaned_data['gsbrightness_system']
        else:
            gstarg, gsra, gsdec, sgsmag, spa = findgs()

        if gstarg != '':
            payload['gstarget'] = gstarg
            payload['gsra'] = gsra
            payload['gsdec'] = gsdec
            payload['gsmags'] = sgsmag
            payload['gsprobe'] = self.cleaned_data['gsprobe']

        payload['posangle'] = spa

        print(payload)

        return payload

class GEMFacility(GenericObservationFacility):
    name = 'GEM'
    form = GEMObservationForm

    @classmethod
    def submit_observation(clz, observation_payload):
        print(PORTAL_URL[get_site(observation_payload['prog'])] + '/too')
        response = make_request(
            'POST',
            PORTAL_URL[get_site(observation_payload['prog'])] + '/too',
            verify=False,
            params=observation_payload
            # headers=clz._portal_headers()
        )
        # Return just observation number
        obsid = response.text.split('-')
        return [obsid[-1]]

    @classmethod
    def validate_observation(clz, observation_payload):
        # Gemini doesn't have an API for validation, but run some checks
        # response = make_request(
        #     'POST',
        #     PORTAL_URL + '/api/userrequests/validate/',
        #     json=observation_payload,
        #     headers=clz._portal_headers()
        # )
        # return response.json()['errors']
        errors = {}
        if 'elevationType' in observation_payload.keys():
            if observation_payload['elevationType'] == 'airmass':
                if float(observation_payload['elevationMin']) < 1.0:
                    errors['elevationMin'] = 'Airmass must be >= 1.0'
                if float(observation_payload['elevationMax']) > 2.5:
                    errors['elevationMax'] = 'Airmass must be <= 2.5'
        return errors

    @classmethod
    def get_observation_url(clz, observation_id):
        # return PORTAL_URL + '/requests/' + observation_id
        return ''

    @classmethod
    def get_terminal_observing_states(clz):
        return TERMINAL_OBSERVING_STATES

    @classmethod
    def get_observing_sites(clz):
        return SITES

    @classmethod
    def get_observation_status(clz, observation_id):
        # response = make_request(
        #     'GET',
        #     PORTAL_URL + '/api/requests/{0}'.format(observation_id),
        #     headers=clz._portal_headers()
        # )
        # return response.json()['state']
        return ''

    @classmethod
    def _portal_headers(clz):
        # if GEM_SETTINGS.get('api_key'):
        #     return {'Authorization': 'Token {0}'.format(GEM_SETTINGS['api_key'])}
        # else:
        #     return {}
        return {}

    @classmethod
    def _archive_headers(clz):
        # if GEM_SETTINGS.get('api_key'):
        #     archive_token = cache.get('GEM_ARCHIVE_TOKEN')
        #     if not archive_token:
        #         response = make_request(
        #             'GET',
        #             PORTAL_URL + '/api/profile/',
        #             headers={'Authorization': 'Token {0}'.format(GEM_SETTINGS['api_key'])}
        #         )
        #         archive_token = response.json().get('tokens', {}).get('archive')
        #         if archive_token:
        #             cache.set('GEM_ARCHIVE_TOKEN', archive_token, 3600)
        #             return {'Authorization': 'Bearer {0}'.format(archive_token)}
        #
        #     else:
        #         return {'Authorization': 'Bearer {0}'.format(archive_token)}
        # else:
        #     return {}
        return {}

    @classmethod
    def data_products(clz, observation_record, product_id=None):
        products = []
        # for frame in clz._archive_frames(observation_record.observation_id, product_id):
        #     products.append({
        #         'id': frame['id'],
        #         'filename': frame['filename'],
        #         'created': frame['DATE_OBS'],
        #         'url': frame['url']
        #     })
        return products

    @classmethod
    def _archive_frames(clz, observation_id, product_id=None):
        # todo save this key somewhere
        frames = []
        # if product_id:
        #     response = make_request(
        #         'GET',
        #         'https://archive-api.GEM.global/frames/{0}/'.format(product_id),
        #         headers=clz._archive_headers()
        #     )
        #     frames = [response.json()]
        # else:
        #     response = make_request(
        #         'GET',
        #         'https://archive-api.GEM.global/frames/?REQNUM={0}'.format(observation_id),
        #         headers=clz._archive_headers()
        #     )
        #     frames = response.json()['results']

        return frames
