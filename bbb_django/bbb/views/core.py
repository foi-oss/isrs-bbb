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

from icalendar import Calendar, Event
from datetime import timedelta
import hashlib

from bbb.models import *

def home_page(request):
    context = RequestContext(request, {
    })
    return render_to_response('home.html', context)

@login_required
def export_meeting(request, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    cal = Calendar()
    cal.add('prodid', '-//commuxi Corporation//bbbforum release//')
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
    event.add('description', 'please join the meeting via %s, the attendee password is "%s"'%\
      (request.build_absolute_uri(reverse('join',args=[meeting_id])), meeting.attendee_password))
    cal.add_component(event)
    print cal.to_ical()
    response = HttpResponse(cal.to_ical(), mimetype='text/calendar')
    response['Content-Disposition'] = 'attachment; filename=%s.ics'%meeting.name
    return response

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

    #meetings = Meeting.objects.all()
    existing = Meeting.objects.filter(user=request.user)
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
                url = meeting.start()

            return HttpResponseRedirect(Meeting.join_url(meeting_id, name, password))
    else:
        form = form_class()

    meeting = Meeting.objects.get(id=meeting_id)
    context = RequestContext(request, {
        'form': form,
        'meeting_name': meeting.name,
        'meeting_id': meeting_id
    })

    return render_to_response('join.html', context)

@login_required
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
            meeting.user = request.user
            meeting.save()
            #url = meeting.start()
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
