#!/bin/sh

while true; do
  date +"%H:%M:%S" >> docker_stats.log
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" >> docker_stats.log
  echo $(tail -n 3 docker_stats.log)
  sleep 2
done
