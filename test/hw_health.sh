#!/bin/sh

while true; do
  echo -n "$(date +"%H:%M:%S"), " >> health.log
  vcgencmd measure_temp | tr -d '\n' >> health.log
  echo -n ", " >> health.log
  vcgencmd get_throttled >> health.log
  echo $(tail -n 1 health.log)
  sleep 10
done
