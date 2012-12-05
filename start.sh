#!/bin/bash
set -e
LOGFILE=/tmp/gunicorn/bbbadmin.log
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=4
USER=bbbadmin
GROUP=bbbadmin

cd /home/bbbadmin
source env/bin/activate
test -d $LOGDIR || mkdir -p $LOGDIR

cd isrs-bbb
exec gunicorn_django -w $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --log-level=debug \
  --log-file=$LOGFILE 2>>$LOGFILE
