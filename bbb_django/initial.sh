#!/bin/bash
`which python` manage.py syncdb
`which python` manage.py schemamigration bbb --initial
echo 'Please update the "SALT" and "BBB_API_URL" in "bbb/local_settings.py"' 

#use manage.py convert_to_south myapp to convert the old app 
