#!/bin/sh

docker exec -it lituya-pg bash

# Create the metrics table
psql -h localhost -U lituya -f metrics.sql lituya
