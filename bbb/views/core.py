from django.http import (Http404, HttpResponseRedirect, HttpResponseNotFound,
                        HttpResponse)
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import login as django_login
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from icalendar import Calendar, Event
from calendar import monthrange
from datetime import timedelta
import hashlib

from bbb.models import *
from bbb.webcalendar import *

import bitly_api

bitly = bitly_api.Connection(access_token='519dc2a8f8e736fca4accd99e7bce356fcdc1fb9')

def home_page(request):
    context = RequestContext(request, {
    })
    return render_to_response('home.html', context)

@login_required
def export_meeting(request, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    cal = Calendar()
    cal.add('prodid', '-//International Student Research Symposium//studentresearchsymposium.com//')
    cal.add('version', '2.0')
    event = Event()
    event.add('summary', meeting.name)
    event.add('dtstart', meeting.start_time)
    if meeting.duration == 0:
        event.add('duration', timedelta(days=1))#unlimit is 1 day by default
    else:
        event.add('duration', timedelta(minutes=meeting.duration))
    #event.add('dtend', '')
    event.add('location', 'http://www.commux.com')
    event.add('description', _('please join the meeting via %(url)s, the attendee password is "%(pwd)s"')%\
      ({'url':request.build_absolute_uri(reverse('join',args=[meeting_id])), 'pwd': meeting.attendee_password}))
    event['uid'] = "%s@%s"%(meeting.id,request.META['HTTP_HOST']) 
    cal.add_component(event)
    #print cal.to_ical()
    response = HttpResponse(cal.to_ical(), mimetype='text/calendar')
    response['Content-Disposition'] = 'attachment; filename=%s.ics'%meeting.name.encode('utf8')
    return response

@login_required
def calendar_today(request):
    d = date.today()
    return calendar(request, d.year, d.month)

@login_required
def calendar(request, year, month):
    y = int(year)
    m = int(month)
    from_date = date(y, m, 1)
    to_date = date(y, m, monthrange(y,m)[1])
    #meetings = Meeting.objects.filter(user=request.user).filter(start_time__gte=from_date, start_time__lte=to_date)
    meetings = Meeting.objects.filter(start_time__gte=from_date, start_time__lte=to_date)
    prev_year = y
    prev_month = m - 1 
    if prev_month == 0:
        prev_month = 12
	prev_year -= 1
    next_year = y
    next_month = m + 1
    if next_month == 13:
        next_month = 1
	next_year += 1
    year_after = y + 1
    year_before = y - 1

    items = request.LANGUAGE_CODE.split('-')
    locale_name = 'en_US.UTF-8'
    if len(items) == 2:
        locale_name = items[0] + '_' + items[1].upper() + '.UTF-8'

    print m,y,prev_month,prev_year,next_month,next_year,year_before,year_after 
    html_calendar = MeetingCalendar(meetings, locale=locale_name).formatmonth(y, m)
    context = RequestContext(request, {
        'Calendar': mark_safe(html_calendar),
        'Month' : m,
        'Year': y,
        'PreviousMonth': prev_month,
        'PreviousYear': prev_year,
        'NextMonth': next_month,
        'NextYear': next_year,
        'YearBeforeThis': year_before,
        'YearAfterThis': year_after,    
    })
    
    return render_to_response('calendar.html', context)

@login_required
def begin_meeting(request):

    if request.method == "POST":
        begin_url = "http://bigbluebutton.org"
        return HttpResponseRedirect(begin_url)

    context = RequestContext(request, {
    })

    return render_to_response('begin.html', context)

@login_required
def meetings(request):

    existing = Meeting.objects.all()
    #existing = Meeting.objects.filter(user=request.user)
    #meetings = Meeting.get_meetings()
    started = Meeting.get_meetings()

    meetings = []
    for meeting in existing:        
        d = {
	    'name': meeting.name,
	    'meeting_id': meeting.id,
	    'info': {
                'moderator_pw': meeting.moderator_password,
	        'attendee_pw': meeting.attendee_password,
                'record': meeting.record,
                'duration': meeting.get_duration_display(),
                'start_time': meeting.start_time,
                'started': meeting.started,
            },
        }

	detail = started.get('%d'%meeting.id)
        print meeting.id, detail
	if detail is not None:
            d['running'] = detail['running']
	    d['info'].update(detail['info'])

        meetings.append(d)

    context = RequestContext(request, {
        'meetings': meetings,
    })

    return render_to_response('meetings.html', context)

def join_meeting(request, meeting_id):
    form_class = Meeting.JoinForm

    if request.method == "POST":
        # Get post data from form
        form = form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            name = data.get('name')
            password = data.get('password')

            meeting = Meeting.objects.get(id=meeting_id)
            if password == meeting.moderator_password:
                #TODO: How to delete the records in db, lazy way?
                #meeting.logout_url = request.build_absolute_uri(reverse('delete',args=[meeting_id, password]))
                meeting.started = True
                meeting.save()
                meeting.start()
            else:
                password = meeting.attendee_password

            return HttpResponseRedirect(Meeting.join_url(meeting_id, name, password))
    else:
        form = form_class()

    meeting = Meeting.objects.get(id=meeting_id)
    short = bitly.shorten("http://bbb.studentresearchsymposium.com/bbb/meeting/%s/join" % meeting_id)
    context = RequestContext(request, {
        'form': form,
        'meeting_name': meeting.name,
        'meeting_id': meeting_id,
        'meeting_share_url': short['url']
    })

    return render_to_response('join.html', context)

@login_required
@permission_required('bbb.end_meeting')
def delete_meeting(request, meeting_id, password):
    if request.method == "POST":
        meeting = Meeting.objects.filter(id=meeting_id)
        meeting.delete()
        Meeting.end_meeting(meeting_id, password)

        msg = _('Successfully ended meeting %s') % meeting_id
        messages.success(request, msg)
        return HttpResponseRedirect(reverse('meetings'))
    else:
        msg = _('Unable to end meeting %s') % meeting_id
        messages.error(request, msg)
        return HttpResponseRedirect(reverse('meetings'))

@login_required
@permission_required('bbb.create_meeting')
def create_meeting(request):
    form_class = Meeting.CreateForm

    if request.method == "POST":
        # Get post data from form
        form = form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            meeting = Meeting()
            meeting.name = data.get('name')
            #password = hashlib.sha1(data.get('password')).hexdigest()
            meeting.attendee_password = data.get('attendee_password')
            meeting.moderator_password = data.get('moderator_password')
            #meeting.meeting_id = data.get('meeting_id')
            meeting.welcome = data.get('welcome')
            meeting.record = data.get('record')
            meeting.duration = data.get('duration')
            meeting.start_time = data.get('start_time')
            meeting.agenda = data.get('agenda')
            meeting.user = request.user
            meeting.save()
            url = meeting.start()
            #msg = _('Successfully created meeting %s') % meeting.name
            msg = _('Successfully schdulered meeting %s') % meeting.name
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('meetings'))
            '''
            try:
                url = meeting.start()
                meeting.save()
                msg = 'Successfully created meeting %s' % meeting.meeting_id
                messages.success(request, msg)
                return HttpResponseRedirect(reverse('meetings'))
            except:
                return HttpResponse("An error occureed whilst creating the " \
                                    "meeting. The meeting has probably been "
                                    "deleted recently but is still running.")
            '''
    else:
        form = form_class()

    context = RequestContext(request, {
        'form': form,
    })

    return render_to_response('create.html', context)
