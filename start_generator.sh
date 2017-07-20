#!/bin/bash

PIDFILE=/var/run/bigpaths_generator.pid

case $1 in
   start)
       /home/ubuntu/bigpaths/generator.py 2>/dev/null &
       echo $! > ${PIDFILE} 
   ;;
   stop)
      kill `cat ${PIDFILE}`
      rm ${PIDFILE}
   ;;
   *)
      echo "usage: {start|stop}" ;;
esac
exit 0
