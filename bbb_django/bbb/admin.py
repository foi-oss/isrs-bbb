# coding: utf-8

from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from bbb.models import Meeting


class MeetingAdmin(admin.ModelAdmin):
    pass

admin.site.register(Meeting, MeetingAdmin)
