# MedDeviceFoS
Feat. of Strength for Medical Device Company Software Developer

## Architectural Overview
![Alt Architectural Diagram](./MedDeviceFoSDiagram.png)

![Alt GET DETAIL API FLOW DIAGRAM](./MedDeviceFoSAPIFlow.png)

## Requirements/Dependencies
- Git
- Docker with Docker Compose


## Development/Deployment Setup

- Git clone this repo
- cd into root of repo
- (on Mac OS or Linux OS):
```
make dev
```
- (on a windows PC)
```
docker compose up --build
```

Note: Hit `Ctrl+C` on this running process to stop

## Run Test

```
make test
```

## Delete/Clean up

Note: This deletes all existing/stored database and patient image data 

```
make clean
```


## UI, API, and Documentation endpoints

Post running deployment step above

UI: `http://localhost`

API: `http://localhost/api/v1`

API DOCS (Swagger UI): `http://localhost/api/v1/docs`
(you can use this docs UI to interactively tryout/play with the backend API)
### Dev Only

Mongodb Access: `mongodb://dev_user:dev_pass@localhost:27017/ion"`

Minio Object Storage UI Access: `http://localhost:9001`
(username: dev_user, pass: dev_pass)

## Postman

If you're able to download Postman, you can import the [collection](IntuitiveIONFoS.postman_collection.json) provided within this git repo
to perform the API calls.

Note: for postman collection you will need to heed the following conventions:
- For the singular Patient GET and the Update (PUT) endpoints you will need to update the endpoint location with the correct UUID in the url
- For the Patients Update (PUT) endpoint, please provide the correct link to the image file in the form data field prior to making the call.


