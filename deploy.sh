#!/bin/sh

OPTIONS="-avzC --exclude-from exclude.txt"
TRANSPORT='ssh -p 22'
CONNECTION='amau@45.33.126.223'
REMOTE_PATH='/home/amau/disaster'

rsync $OPTIONS -e "$TRANSPORT" . $CONNECTION:$REMOTE_PATH