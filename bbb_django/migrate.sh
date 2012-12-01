#!/bin/bash

sudo /home/jeromy/dev/bbb_python/env/bin/python manage.py schemamigration bbb --auto
sudo /home/jeromy/dev/bbb_python/env/bin/python manage.py migrate bbb
