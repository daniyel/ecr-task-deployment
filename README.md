# ecr-task-deployment

This project will create Lambda function that updates task, whenever we push new image into ECR.

### Prerequisites

* [AWS CLI](https://aws.amazon.com/cli/) - The AWS Command Line Interface (CLI)

## Getting Started

We need to do this only once. If there is same stack already running on AWS, we do not need to do anything.

### First time setup

Run `make upload` (this will create S3 bucket, if it does not already exist, upload CloudFormation template and Lambda function).

Go to AWS Console under CloudFormation, choose create stack and check last option (`Specify an Amazon S3 template URL`) under `Choose a template`.
Paste a link form S3 bucket where the CloudFormation `template.yaml` was uploaded to.
Proceed to the next step by clicking `Next`. Under stack name you can type something like `EcrTaskDeployment`. That's it.

Everything else should be created and set automatically.

This stack updates tasks on both `development` and `production` ECS cluster environments.

### Explanation

If you have a `development` and `production` ECS clusters, this setup will update tasks on both ECS environments.
One prerequisiteis needed, for this to be achievable. We need to tag our Docker images with either `:development` or `:production` tags.

As for lambda function goes, we need to pass `CLUSTER_SUFFIX` environment variable. 
So in case we have ECS cluster named `development-ecs` and `production-ecs`, we need to pass to lambda just `ecs` and it will be concatenated automatically.
