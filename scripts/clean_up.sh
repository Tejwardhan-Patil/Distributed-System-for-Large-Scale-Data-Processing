#!/bin/bash

# Script to clean up resources after testing or deployment

echo "Starting cleanup process..."

# Stop any running services (Docker, Kubernetes, etc.)
echo "Stopping Docker containers..."
docker-compose down

echo "Stopping Kubernetes deployments..."
kubectl delete -f deployment/kubernetes/k8s_deployment.yaml

# Remove any Docker images built during deployment
echo "Removing Docker images..."
docker images -q --filter "dangling=true" | xargs docker rmi -f

# Delete temporary files or logs from the system
echo "Cleaning up temporary files..."
find /tmp -type f -name "*.log" -exec rm -f {} \;

# Remove old deployment resources
echo "Removing old Helm releases..."
helm uninstall my-release

echo "Cleaning up old Terraform resources..."
terraform destroy -auto-approve

# Remove outdated data from storage
echo "Cleaning up outdated data from storage..."
sh utils/scripts/CleanupOldData.sh

# Optionally remove cloud resources provisioned during tests
echo "Cleaning up cloud resources with CloudFormation..."
aws cloudformation delete-stack --stack-name my-stack

# Confirm completion
echo "Cleanup process completed."