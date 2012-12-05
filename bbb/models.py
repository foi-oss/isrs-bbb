from django.db import models
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from urllib import urlencode
from hashlib import sha1
import xml.etree.ElementTree as ET
import random
import datetime

import requests

MEETING_DURATION = (
  (0, _('unlimited')),
  (15, _('15 min')),
  (30, _('30 min')),
  (60, _('1 hour')),
  (120, _('2 hour')),
  (180, _('3 hour')),
)

class Meeting(models.Model):
  user        = models.ForeignKey(User, verbose_name=_('user'))
  name        = models.CharField(max_length=100, verbose_name=_('meeting name'))
  attendee_password = models.CharField(max_length=50, verbose_name=_('attendee password'))
  moderator_password = models.CharField(max_length=50, verbose_name=_('moderator password'))
  welcome     = models.CharField(max_length=100, blank=True, verbose_name=_('welcome message'))
  record      = models.BooleanField(default=False, verbose_name=_('record'))
  duration    = models.IntegerField(default=0, choices=MEETING_DURATION, verbose_name=_('duration'))
  start_time  = models.DateTimeField(verbose_name=_('start time'))
  started     = models.BooleanField(default=False, verbose_name=_('started'))
  agenda      = models.CharField(max_length=1000, blank=True, verbose_name=_('agenda'))

  class Meta:
    verbose_name = _('meeting')
    verbose_name_plural = _('meetings')
    permissions = (('create_meeting', 'Can create meeting'),
                   ('end_meetnig', 'Can end meeting'))

  @classmethod
  def api_call(self, call, query):
    query['checksum'] = sha1(call + urlencode(query) + settings.SALT).hexdigest()
    print 'BBB API REQUEST', call, query
    rq = requests.get(settings.BBB_API_URL + "/" + call, params=query)
    print 'BBB API RESP', rq.ok
    
    if rq.ok != False:
      xml = ET.XML(rq.text)
      code = xml.find('returncode').text

      if code == 'SUCCESS':
        return xml
      else:
        return None
    else:
      return None

  def is_running(self):
    result = self.api_call('isMeetingRunning', {'meetingID': self.id})
    if result:
      return result.find('running').text
    else:
      return 'error'

  @classmethod
  def end_meeting(self, meeting_id, password):
    result = self.api_call('end', {'meetingID': meeting_id,
                                   'password': password})
    return 'error' if result == None else True

  @classmethod
  def meeting_info(self, meeting_id, password):
    r = self.api_call('getMeetingInfo', {'meetingID': meeting_id,
                                              'password': password})
    if r == None:
      return None

    return {
      'start_time':           r.find('startTime').text,
      'end_time':             r.find('endTime').text,
      'participant_count':    r.find('participantCount').text,
      'moderator_count':      r.find('moderatorCount').text,
      'moderator_pw':         r.find('moderatorPW').text,
      'attendee_pw':          r.find('attendeePW').text,
      'invite_url':           reverse('join', args=[meeting_id]),
    }

  @classmethod
  def get_meetings(self):
    result = self.api_call('getMeetings', {'random': random.randint(0, 4444)})
    if result == None:
      return 'error'

    # Create dict of values for easy use in template
    d = {}
    r = result[1].findall('meeting')
    for m in r:
      meeting_name = m.find('meetingName').text
      meeting_id = m.find('meetingID').text
      password = m.find('moderatorPW').text
      d[meeting_id] = {
        'name':         meeting_name,
        'meeting_id':   meeting_id,
        'running':      m.find('running').text,
        'info':         Meeting.meeting_info(meeting_id, password)
        #'moderator_pw': password,
        #'attendee_pw': m.find('attendeePW').text,
      }

    return d

  def start(self):
    voicebridge = 70000 + random.randint(0, 9999)
    result = self.api_call('create', {
      'name':        self.name.encode('utf8'),
      'meetingID':   self.id,
      'attendeePW':  self.attendee_password,
      'moderatorPW': self.moderator_password,
      'voiceBridge': voicebridge,
      'welcome':     self.welcome.encode('utf8'),
      'record':      self.record,
      #{'duration', self.duration),
    })

    if result:
      return result
    else:
      raise

  @classmethod
  def join_url(self, meeting_id, name, password):
    query = urlencode({
      'fullName':   name.encode('utf8'),
      'meetingID':  meeting_id,
      'password':   password,
    })
    checksum = sha1("join" + query + settings.SALT).hexdigest()

    return "%s/join?%s&checksum=%s" % (settings.BBB_API_URL, query, checksum)

  class CreateForm(forms.Form):
    name = forms.CharField(label=_('meeting name'))
    attendee_password   = forms.CharField(label=_('attendee password'),
                                          widget=forms.PasswordInput(render_value=False))
    moderator_password  = forms.CharField(label=_('moderator password'),
                                           widget=forms.PasswordInput(render_value=False))
    welcome             = forms.CharField(label=_('welcome message'), initial=_('Welcome!'))
    record              = forms.BooleanField(label=_('record'), initial=False, required=False)
    duration            = forms.ChoiceField(label=_('duration'), choices=MEETING_DURATION)
    start_time          = forms.DateTimeField(label=_('start time'), widget=widgets.AdminSplitDateTime())
    agenda              = forms.CharField(label=_('agenda'), required=False, widget=forms.Textarea)
   
    def clean(self):
      data = self.cleaned_data

      # TODO: should check for errors before modifying
      #data['meeting_id'] = data.get('name')

      #if Meeting.objects.filter(name = data.get('name')):
      #    raise forms.ValidationError("That meeting name is already in use")
      return data

  class JoinForm(forms.Form):
    name = forms.CharField(label=_("Your name"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False),
                               required=False)
