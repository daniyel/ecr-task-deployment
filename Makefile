AWS_REGION ?= eu-central-1
AWS_ACCOUNT_ID ?= <AWS_ACCOUNT_ID>
ARCHIVE_NAME ?= deploy_handler.zip
TEMPLATE ?= template.yaml
LAMBDA_FILE_NAME ?= deploy_handler.py
S3_BUCKET ?= ecr-task-deployment

upload: create_bucket pack
	aws s3 cp ./aws/$(TEMPLATE) s3://$(S3_BUCKET)/aws/$(TEMPLATE)
	aws s3 cp ./$(ARCHIVE_NAME) s3://$(S3_BUCKET)/$(ARCHIVE_NAME)
	rm -rf ./$(ARCHIVE_NAME)

pack:
	zip -r ./$(ARCHIVE_NAME) ./lambda/$(LAMBDA_FILE_NAME)

DECODED_PASSWORD = $(shell aws ecr get-authorization-token --output text --query 'authorizationData[].authorizationToken' | base64 -D | cut -d: -f2)

reauth:
	docker login -u AWS -p $(DECODED_PASSWORD) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

BUCKET_EXISTS = $(shell aws s3 ls s3://$(S3_BUCKET) 2>&1 | grep -c NoSuchBucket)

create_bucket:
ifeq ($(strip $(BUCKET_EXISTS)),1)
	aws s3api create-bucket --bucket $(S3_BUCKET) --region $(AWS_REGION) --create-bucket-configuration LocationConstraint=$(AWS_REGION)
endif
