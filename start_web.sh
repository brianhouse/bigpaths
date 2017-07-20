#!/bin/bash

PIDFILE=/var/run/bigpaths_web.pid

case $1 in
   start)
       /home/ubuntu/bigpaths/main.py 2>/dev/null &
       echo $! > ${PIDFILE} 
   ;;
   stop)
      kill `cat ${PIDFILE}`
      rm ${PIDFILE}
   ;;
   *)
      echo "usage: main {start|stop}" ;;
esac
exit 0
