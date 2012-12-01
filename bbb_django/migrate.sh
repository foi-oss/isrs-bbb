#!/bin/bash

sudo `which python` manage.py schemamigration bbb --auto
sudo `which python` manage.py migrate bbb
