
pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '025881472816.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'aws-devops-app'
        IMAGE_TAG = 'v2'
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
                sh 'docker build -t aws-devops-app:v2 .'
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
                      aws-devops-app:v2

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
                    docker tag aws-devops-app:v2 $ECR_IMAGE
                    docker push $ECR_IMAGE
                '''
            }
        }

        stage('Deploy to ECS') {
            steps {
                echo 'Deploying application to ECS Fargate'

                sh '''
                    aws ecs update-service \
                      --cluster aws-devops-cluster \
                      --service aws-devops-service \
                      --force-new-deployment \
                      --region $AWS_REGION

                    aws ecs wait services-stable \
                      --cluster aws-devops-cluster \
                      --services aws-devops-service \
                      --region $AWS_REGION
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

