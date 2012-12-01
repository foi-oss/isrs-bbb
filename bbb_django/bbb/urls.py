from django.conf.urls.defaults import *
#from bbb.views.core import (home_page, create_meeting, begin_meeting, meetings, join_meeting, delete_meeting, export_meeting)
from bbb.views.core import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import settings

def i18n_javascript(request):
    return admin.site.i18n_javascript(request)

urlpatterns = patterns('',
    url('^$', home_page, name='home'),
    url(r'^login/$', 'django.contrib.auth.views.login', {
            'template_name': 'login.html',
        }, name='login'),
    url(r'^logoff/$', 'django.contrib.auth.views.logout', {'next_page': '/'},
        name='logout'),
    url('^create/$', create_meeting, name='create'),
    #url('^begin/$', begin_meeting, name='begin'),
    url('^calendar/(?P<year>\d+)/(?P<month>\d+)/$', calendar, name='calendar'),
    url('^calendar/$', calendar_today, name='calendar_today'),
    url('^meetings/$', meetings, name='meetings'),
    url('^meeting/(?P<meeting_id>[a-zA-Z0-9 _-]+)/export$', export_meeting, name='export'),
    url('^meeting/(?P<meeting_id>[a-zA-Z0-9 _-]+)/join$', join_meeting, name='join'),
    url('^meeting/(?P<meeting_id>[a-zA-Z0-9 _-]+)/(?P<password>.*)/delete$', delete_meeting,
        name='delete'),
    url('^help.html$', 'django.views.generic.simple.redirect_to', {
            'url': 'http://www.bbbforum.com' ,
        }, name='help'),
 
    (r'^admin/jsi18n', i18n_javascript),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
)
