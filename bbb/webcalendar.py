from calendar import LocaleHTMLCalendar
from datetime import date,datetime
from itertools import groupby
from django.core.urlresolvers import reverse

#from django.utils.html import conditional_escape as esc

class MeetingCalendar(LocaleHTMLCalendar):

    def __init__(self, meetings, *args, **kwargs):
        super(MeetingCalendar, self).__init__(*args, **kwargs)
        self.meetings = self.group_by_day(meetings)
        #print self.workouts

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            d = date(self.year, self.month, day)
            if date.today() == d:
                cssclass += ' today'
            if d in self.meetings:
                cssclass += ' filled'
                body = ['<ul>']
                for meeting in self.meetings[d]:
                    body.append('<li>')
                    body.append('<a href="%s">' % reverse('join',args=[meeting.id]) )
                    body.append('[%s]-%s'%(meeting.start_time.time(), meeting.name))
                    body.append('</a></li>')
                body.append('</ul>')
                return self.day_cell(cssclass, '%d %s' % (day, ''.join(body)))
            return self.day_cell(cssclass, day)
        return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(MeetingCalendar, self).formatmonth(year, month)

    def group_by_day(self, meetings):
        field = lambda meeting: meeting.start_time.date()
        return dict(
            [(day, list(items)) for day, items in groupby(meetings, field)]
        )

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)

