import os
import boto3
from botocore.exceptions import ClientError

def get_task_definitions(ecs, image, image_tag):
    response = ecs.list_task_definition_families(status='ACTIVE')
    families = response['families']
    while ('nextToken' in response):
        response = ecs.list_task_definition_families(nextToken=response['nextToken'])
        families.append(response['families'])

    task_defs = [ecs.describe_task_definition(taskDefinition=family)['taskDefinition'] for family in families]
    return [
        task_def for task_def in task_defs
        if any([
            container_def for container_def in task_def['containerDefinitions']
            if container_def['image'].startswith(image) and container_def['image'].endswith(f':{image_tag}')
        ])
    ]

def update_container_definition(container_def, image, image_tag):
    print(f'Update container definition to {image}:{image_tag}')
    container_def['image'] = f'{image}:{image_tag}'

def strip_arn(arn):
    return arn[:arn.rindex(":")]

def update_task_definition(ecs, task_def, new_task_defs, image, image_tag):
    family = task_def['family']
    container_defs = task_def['containerDefinitions']
    print(f'Update task definition: {family}')
    [
        update_container_definition(container_def, image, image_tag)
        for container_def in container_defs
        if container_def['image'].startswith(image)
    ]

    response = ecs.register_task_definition(
        family=family,
        taskRoleArn=task_def['taskRoleArn'],
        containerDefinitions=container_defs,
        volumes=task_def['volumes'],
        placementConstraints=task_def['placementConstraints'],
        requiresCompatibilities=task_def['compatibilities'])
    old_task_def_arn = task_def['taskDefinitionArn']
    new_task_def_arn = response['taskDefinition']['taskDefinitionArn']
    new_task_defs[strip_arn(old_task_def_arn)] = new_task_def_arn
    return new_task_def_arn

def get_services(ecs, cluster):
    response = ecs.list_services(cluster=cluster)
    service_arns = response['serviceArns']
    while ('nextToken' in response):
        response = ecs.list_services(cluster=cluster, nextToken=response['nextToken'])
        service_arns.append(response['serviceArns'])
    return [
        service for service in ecs.describe_services(cluster=cluster, services=service_arns)['services']
        if service['status'] == 'ACTIVE'
    ]

def update_service(ecs, cluster, service, new_task_def_arn):
    service_arn = service['serviceArn']
    print(f'Update service {service_arn} with {new_task_def_arn}')
    ecs.update_service(cluster=cluster, service=service_arn, taskDefinition=new_task_def_arn)

def lambda_handler(event, context):
    cluster_suffix = os.environ['CLUSTER_SUFFIX']

    region = event['region']
    ecs = boto3.client('ecs', region_name=region)
    ecr = boto3.client('ecr', region_name=region)

    response_image = event['detail']['responseElements']['image']

    repository_name = response_image['repositoryName']
    registry_id = response_image['registryId']
    image = f'{registry_id}.dkr.ecr.{region}.amazonaws.com/{repository_name}'
    image_tag = response_image['imageId']['imageTag']
    image_manifest = response_image['imageManifest']
    cluster = f'{image_tag}-{cluster_suffix}'

    # Update Task Definitions
    task_definitions = get_task_definitions(ecs, image, image_tag)

    new_task_definitions = {}
    [update_task_definition(ecs, task_definition, new_task_definitions, image, image_tag) for task_definition in task_definitions]

    if new_task_definitions:
        services = get_services(ecs, cluster)
        # Update services
        [
            update_service(ecs, cluster, service, new_task_definitions[strip_arn(service['taskDefinition'])])
            for service in services
            if strip_arn(service['taskDefinition']) in new_task_definitions.keys()
        ]
