#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define variables
K8S_NAMESPACE="data-processing-system"
HELM_CHART_PATH="../deployment/kubernetes/helm_chart"
DOCKER_IMAGE="website.com/data-processing-system:latest"
DOCKERFILE_PATH="../deployment/docker/Dockerfile"
K8S_DEPLOYMENT_FILE="../deployment/kubernetes/k8s_deployment.yaml"
TERRAFORM_PATH="../deployment/terraform"
ANSIBLE_PLAYBOOK="../deployment/ansible/server_setup.yml"

echo "Starting deployment process..."

# Provision Infrastructure using Terraform
echo "Provisioning cloud infrastructure with Terraform..."
cd $TERRAFORM_PATH
terraform init
terraform apply -auto-approve
echo "Infrastructure provisioned successfully."

# Build Docker Image
echo "Building Docker image..."
cd ../docker/
docker build -t $DOCKER_IMAGE -f $DOCKERFILE_PATH .
docker push $DOCKER_IMAGE
echo "Docker image built and pushed: $DOCKER_IMAGE"

# Deploy Application to Kubernetes Cluster
echo "Deploying application to Kubernetes..."
kubectl create namespace $K8S_NAMESPACE || echo "Namespace already exists"
kubectl config set-context --current --namespace=$K8S_NAMESPACE

# Deploy Helm Chart
echo "Deploying Helm chart..."
helm upgrade --install data-processing $HELM_CHART_PATH --namespace $K8S_NAMESPACE
echo "Helm chart deployed successfully."

# Apply Kubernetes Configuration
echo "Applying Kubernetes deployment configuration..."
kubectl apply -f $K8S_DEPLOYMENT_FILE
echo "Kubernetes deployment configuration applied successfully."

# Set up Ansible for server configuration 
echo "Running Ansible playbook for server configuration..."
ansible-playbook -i ../ansible/hosts $ANSIBLE_PLAYBOOK
echo "Ansible playbook executed successfully."

# Verify Deployment
echo "Verifying deployment..."
kubectl rollout status deployment/data-processing
kubectl get pods -n $K8S_NAMESPACE
kubectl get services -n $K8S_NAMESPACE

echo "Deployment successful."