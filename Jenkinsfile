
pipeline {
    agent any

   environment {
    AWS_REGION = 'ap-south-1'
    ECR_REGISTRY = '025881472816.dkr.ecr.ap-south-1.amazonaws.com'
    ECR_REPOSITORY = 'aws-devops-app'
    IMAGE_TAG = "build-${BUILD_NUMBER}"
    ECR_IMAGE = "${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"
}

    stages {
        stage('Checkout') {
            steps {
                echo 'Fetching source code from GitHub'
                checkout scm
            }
        }

        stage('Validate Python') {
            steps {
                sh 'python3 -m py_compile app.py'
            }
        }

        stage('Build Docker Image') {
    steps {
        sh 'docker build -t aws-devops-app:$IMAGE_TAG .'
    }
}

        stage('Test Application') {
            steps {
                sh '''
                    set -e
                    docker rm -f ci-test-app 2>/dev/null || true

                    docker run -d \
                      --name ci-test-app \
                      -p 127.0.0.1:5001:5000 \
                      aws-devops-app:$IMAGE_TAG

                    trap 'docker rm -f ci-test-app >/dev/null 2>&1 || true' EXIT

                    for i in $(seq 1 15); do
                        if curl -fsS http://127.0.0.1:5001/health; then
                            exit 0
                        fi
                        sleep 2
                    done

                    echo "Health check failed"
                    exit 1
                '''
            }
        }

        stage('Login to AWS ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region $AWS_REGION |
                    docker login --username AWS --password-stdin $ECR_REGISTRY
                '''
            }
        }

        stage('Tag and Push to ECR') {
    steps {
        sh '''
            docker tag aws-devops-app:$IMAGE_TAG $ECR_IMAGE
            docker push $ECR_IMAGE
        '''
    }
}


stage('Deploy to ECS') {
    steps {
        echo 'Deploying unique Docker image to ECS Fargate'

        sh '''
            set -e

            echo "Retrieving current ECS task definition..."

            aws ecs describe-task-definition \
              --task-definition aws-devops-task \
              --region $AWS_REGION \
              --query taskDefinition \
              --output json > task-definition.json

            echo "Updating container image to $ECR_IMAGE"

            python3 - "$ECR_IMAGE" <<'PY'
import json
import sys

image = sys.argv[1]
path = "task-definition.json"

with open(path) as f:
    task = json.load(f)

container_found = False

for container in task["containerDefinitions"]:
    if container["name"] == "aws-devops-container":
        container["image"] = image
        container_found = True

if not container_found:
    raise SystemExit("ERROR: ECS container not found")

for key in [
    "taskDefinitionArn",
    "revision",
    "status",
    "requiresAttributes",
    "compatibilities",
    "registeredAt",
    "registeredBy"
]:
    task.pop(key, None)

with open(path, "w") as f:
    json.dump(task, f)

print("Task definition updated successfully")
PY

            echo "Registering new ECS task definition..."

            NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
              --cli-input-json file://task-definition.json \
              --region $AWS_REGION \
              --query 'taskDefinition.taskDefinitionArn' \
              --output text)

            echo "New task definition: $NEW_TASK_DEF_ARN"

            echo "Updating ECS service..."

            aws ecs update-service \
              --cluster aws-devops-cluster \
              --service aws-devops-service \
              --task-definition "$NEW_TASK_DEF_ARN" \
              --region $AWS_REGION

            echo "Waiting for ECS deployment..."

            for i in $(seq 1 60); do

                ROLLOUT=$(aws ecs describe-services \
                  --cluster aws-devops-cluster \
                  --services aws-devops-service \
                  --region $AWS_REGION \
                  --query 'services[0].deployments[?status==`PRIMARY`].rolloutState | [0]' \
                  --output text)

                RUNNING=$(aws ecs describe-services \
                  --cluster aws-devops-cluster \
                  --services aws-devops-service \
                  --region $AWS_REGION \
                  --query 'services[0].runningCount' \
                  --output text)

                DESIRED=$(aws ecs describe-services \
                  --cluster aws-devops-cluster \
                  --services aws-devops-service \
                  --region $AWS_REGION \
                  --query 'services[0].desiredCount' \
                  --output text)

                PENDING=$(aws ecs describe-services \
                  --cluster aws-devops-cluster \
                  --services aws-devops-service \
                  --region $AWS_REGION \
                  --query 'services[0].pendingCount' \
                  --output text)

                echo "Rollout: $ROLLOUT | Running: $RUNNING | Desired: $DESIRED | Pending: $PENDING"

                if [ "$ROLLOUT" = "COMPLETED" ] && \
                   [ "$RUNNING" = "$DESIRED" ] && \
                   [ "$PENDING" = "0" ]; then
                    echo "ECS deployment completed successfully!"
                    exit 0
                fi

                if [ "$ROLLOUT" = "FAILED" ]; then
                    echo "ECS deployment failed!"
                    exit 1
                fi

                sleep 15
            done

            echo "ECS deployment timed out after 15 minutes."
            exit 1
        '''
    }
}
            }

    post {
        success {
            echo 'CI/CD pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Check Console Output.'
        }
    }
}
