#!/bin/sh

docker run --name lituya-pg -e POSTGRES_PASSWORD=lituya -e POSTGRES_DB=lituya -e POSTGRES_USER=lituya -e PGDATA=/pgdata -v lituya_data:/pgdata --expose 5432 -p 5432:5432 --network lituya_net -d postgres
docker run -d --name=grafana -p 3000:3000 --network lituya_net grafana/grafana
