# Author: Suraj Ravichandran
# 01/19/2024
# FoS for Intuitive Surgical

# Bring up a live reloading enabled dev instance up
dev:
	docker-compose up --build

# Delete all local containers, local volumes, and minio persistent data storage
clean:
	docker compose rm --volumes --stop --force
	cd ./backend/minio_container_data_persistence && rm -rf -- ..?* .[!.]* ./*
