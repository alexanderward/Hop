import boto3

from settings import APP


def get_helper(service):
	if service == 'ec2':
		return AWSHelper.EC2
	elif service == 'rds':
		return AWSHelper.RDS


class AWSHelper(object):
	class EC2(object):
		client = boto3.resource('ec2')
		client2 = boto3.client('ec2')

		@staticmethod
		def get_instances(stack, tags=None, running=False):
			if tags is None:
				tags = {}
			filters = [
				{"Name": "tag:stack", "Values": [stack]},
				{"Name": "tag:app", "Values": [APP]},
			]
			if running:
				filters.append({'Name': 'instance-state-name', 'Values': ['running']})
			for tag, values in tags.items():
				filters.append({"Name": "tag:{}".format(tag), "Values": values})
			return AWSHelper.EC2.client.instances.filter(Filters=filters)

		@staticmethod
		def start_instances(instance_ids):
			return AWSHelper.EC2.client2.start_instances(InstanceIds=instance_ids, DryRun=False)

		@staticmethod
		def stop_instances(instance_ids):
			return AWSHelper.EC2.client2.stop_instances(InstanceIds=instance_ids, DryRun=False)

	class RDS(object):
		client = boto3.client('rds')

		@staticmethod
		def get_instances(stack, running=False):
			def get_tags_for_db(db):
				tmp = {}
				instance_arn = db['DBInstanceArn']
				instance_tags = AWSHelper.RDS.client.list_tags_for_resource(ResourceName=instance_arn)
				for row in instance_tags['TagList']:
					tmp[row['Key']] = row['Value']
				return instance_tags['TagList'], tmp

			filters = []
			if running:
				filters.append({'Name': 'instance-state-name', 'Values': ['running']})
			instances = AWSHelper.RDS.client.describe_db_instances(Filters=filters)
			if instances:
				instances = instances['DBInstances']

			rds_instances = []
			for instance in instances:
				tags, mapped = get_tags_for_db(instance)
				if mapped.get('app') == APP and mapped.get('stack') == stack:
					tag_list = []
					for tag in tags:
						if tag['Key'] not in ['app', 'stack']:
							tag_list.append(tag)
					rds_instances.append({'instance': instance, 'tags': tag_list})
			return rds_instances

		@staticmethod
		def start_instances(instance_ids):
			for instance_id in instance_ids:
				AWSHelper.RDS.client.start_db_instance(DBInstanceIdentifier=instance_id)

		@staticmethod
		def stop_instances(instance_ids):
			for instance_id in instance_ids:
				AWSHelper.RDS.client.stop_db_instance(DBInstanceIdentifier=instance_id)
