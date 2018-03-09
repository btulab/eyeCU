#!/bin/bash

curl -X POST -F "temperature=23" -F "co2=100" -F "pressure=90000" -F "humidity=77" -F "altitude=5500" -F "sound=1" -F "MAC=DE:AD:BE:EF:00:00" -F "voc=20" -F "button=1" -F "light=50" -F "motion=1" localhost:5000
