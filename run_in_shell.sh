#!/bin/bash

# A script to set current date and time from epoch UTC time if argument type is String or shutdown device if string
# Before using this script, please, set root permissions:
# sudo chown root:root script_name.sh
# sudo chmod 700 script_name.sh

if [ $1 -eq $1 2> /dev/null ]; then
	date -s @$1
else
	init 0
fi
