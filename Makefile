DOCKER_IMAGE_NAME=chatendpoint-lambda
CURR_LOCATION=$(shell pwd)

build:
	DOCKER_BUILDKIT=1 docker build --file Dockerfile --output out .

deploy:
	aws s3 cp out/package.zip s3://lambda-deployments-zihao1 --profile localzone-project
	aws lambda update-function-code --function-name chat-endpoint --s3-bucket lambda-deployments-zihao1 --s3-key package.zip --profile localzone-project
	# rm -rf out


all: build deploy