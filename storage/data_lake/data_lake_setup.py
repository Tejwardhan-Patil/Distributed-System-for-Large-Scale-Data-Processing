import boto3
import logging
import json

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data_lake_setup")

# AWS Clients for S3, LakeFormation, IAM, and Glue
s3_client = boto3.client('s3')
lake_formation_client = boto3.client('lakeformation')
iam_client = boto3.client('iam')
glue_client = boto3.client('glue')

# Function to create an S3 bucket
def create_s3_bucket(bucket_name, region):
    try:
        response = s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        logger.info(f"S3 bucket '{bucket_name}' created successfully.")
        return response
    except Exception as e:
        logger.error(f"Failed to create S3 bucket: {e}")
        raise

# Function to create IAM role for LakeFormation and Glue access
def create_iam_role(role_name, policy_arn):
    try:
        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lakeformation.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
        )
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        logger.info(f"IAM role '{role_name}' created and policy attached.")
        return role
    except Exception as e:
        logger.error(f"Failed to create IAM role: {e}")
        raise

# Function to register S3 location in LakeFormation
def register_s3_location(s3_arn, role_arn):
    try:
        response = lake_formation_client.register_resource(
            ResourceArn=s3_arn,
            RoleArn=role_arn
        )
        logger.info(f"S3 location '{s3_arn}' registered in LakeFormation.")
        return response
    except Exception as e:
        logger.error(f"Failed to register S3 location: {e}")
        raise

# Function to create Glue Data Catalog Database
def create_glue_database(database_name):
    try:
        response = glue_client.create_database(
            DatabaseInput={'Name': database_name}
        )
        logger.info(f"Glue database '{database_name}' created.")
        return response
    except Exception as e:
        logger.error(f"Failed to create Glue database: {e}")
        raise

# Function to set LakeFormation permissions
def set_lakeformation_permissions(principal, resource, permissions):
    try:
        response = lake_formation_client.grant_permissions(
            Principal={'DataLakePrincipalIdentifier': principal},
            Resource=resource,
            Permissions=permissions
        )
        logger.info(f"Permissions set for principal '{principal}'.")
        return response
    except Exception as e:
        logger.error(f"Failed to set permissions: {e}")
        raise

# Function to create an S3 bucket policy
def create_s3_bucket_policy(bucket_name, policy_document):
    try:
        response = s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=policy_document
        )
        logger.info(f"Bucket policy set for '{bucket_name}'.")
        return response
    except Exception as e:
        logger.error(f"Failed to create bucket policy: {e}")
        raise

# Function to create and setup a data lake
def setup_data_lake(bucket_name, region, role_name, policy_arn, database_name):
    try:
        # Create S3 bucket for data storage
        create_s3_bucket(bucket_name, region)
        bucket_arn = f"arn:aws:s3:::{bucket_name}"

        # Create IAM role for LakeFormation and Glue
        role = create_iam_role(role_name, policy_arn)
        role_arn = role['Role']['Arn']

        # Register S3 location with LakeFormation
        register_s3_location(bucket_arn, role_arn)

        # Create Glue database for metadata management
        create_glue_database(database_name)

        # Grant LakeFormation permissions to the IAM role
        set_lakeformation_permissions(
            principal=role_arn,
            resource={'Database': {'Name': database_name}},
            permissions=['ALL']
        )

        logger.info("Data lake setup completed successfully.")
    except Exception as e:
        logger.error(f"Data lake setup failed: {e}")

# Main execution
if __name__ == "__main__":
    # Configuration parameters
    BUCKET_NAME = "my-data-lake-bucket"
    REGION = "us-west-2"
    ROLE_NAME = "LakeFormationGlueRole"
    POLICY_ARN = "arn:aws:iam::aws:policy/service-role/AWSLakeFormationDataAdmin"
    DATABASE_NAME = "data_lake_db"

    # Run data lake setup
    setup_data_lake(BUCKET_NAME, REGION, ROLE_NAME, POLICY_ARN, DATABASE_NAME)

# Function to delete the S3 bucket
def delete_s3_bucket(bucket_name):
    try:
        response = s3_client.delete_bucket(Bucket=bucket_name)
        logger.info(f"S3 bucket '{bucket_name}' deleted successfully.")
        return response
    except Exception as e:
        logger.error(f"Failed to delete S3 bucket: {e}")
        raise

# Function to remove LakeFormation resources
def deregister_s3_location(s3_arn):
    try:
        response = lake_formation_client.deregister_resource(ResourceArn=s3_arn)
        logger.info(f"S3 location '{s3_arn}' deregistered from LakeFormation.")
        return response
    except Exception as e:
        logger.error(f"Failed to deregister S3 location: {e}")
        raise

# Function to delete Glue database
def delete_glue_database(database_name):
    try:
        response = glue_client.delete_database(Name=database_name)
        logger.info(f"Glue database '{database_name}' deleted.")
        return response
    except Exception as e:
        logger.error(f"Failed to delete Glue database: {e}")
        raise

# Cleanup function to delete data lake setup
def cleanup_data_lake(bucket_name, database_name):
    try:
        bucket_arn = f"arn:aws:s3:::{bucket_name}"

        # Delete Glue database
        delete_glue_database(database_name)

        # Deregister S3 location from LakeFormation
        deregister_s3_location(bucket_arn)

        # Delete S3 bucket
        delete_s3_bucket(bucket_name)

        logger.info("Data lake cleanup completed successfully.")
    except Exception as e:
        logger.error(f"Data lake cleanup failed: {e}")