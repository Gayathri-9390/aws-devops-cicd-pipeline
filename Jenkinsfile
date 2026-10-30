pipeline {
    agent any

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
                echo 'Python validation successful'
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

                    echo "Application health check failed"
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'CI pipeline completed successfully!'
        }

        failure {
            echo 'CI pipeline failed. Check the console output.'
        }
    }
}
