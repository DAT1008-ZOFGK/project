pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'music-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
        POSTGRES_PASSWORD = credentials('postgres-password')
        JWT_SECRET = credentials('jwt-secret')
        SONAR_TOKEN = credentials('sonar-token')
    }
    
    stages {
        stage('Code Quality Check') {
            steps {
                // Chạy pylint để kiểm tra code quality
                sh 'pip install pylint'
                sh 'pylint app/'
                
                // SonarQube analysis
                sh """
                    sonar-scanner \
                    -Dsonar.projectKey=music-app \
                    -Dsonar.sources=. \
                    -Dsonar.host.url=http://sonarqube:9000 \
                    -Dsonar.login=$SONAR_TOKEN
                """
            }
        }
        
        stage('Unit Tests') {
            steps {
                // Chạy unit tests với pytest và tạo coverage report
                sh '''
                    pip install pytest pytest-cov
                    pytest app/tests/ --cov=app --cov-report=xml
                '''
            }
            post {
                always {
                    // Publish test results
                    junit 'test-results/*.xml'
                    // Publish coverage report
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                // Chạy safety check cho Python dependencies
                sh 'pip install safety'
                sh 'safety check'
                
                // Scan Docker image với Trivy
                sh '''
                    trivy image $DOCKER_IMAGE:$DOCKER_TAG
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                // Build và tag Docker image
                sh 'docker build -t $DOCKER_IMAGE:$DOCKER_TAG ./app'
                sh 'docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest'
            }
        }
        
        stage('Push Docker Image') {
            steps {
                // Push image lên registry
                withDockerRegistry(credentialsId: 'docker-cred', url: '') {
                    sh '''
                        docker push $DOCKER_IMAGE:$DOCKER_TAG
                        docker push $DOCKER_IMAGE:latest
                    '''
                }
            }
        }
        
        stage('Deploy Database') {
            steps {
                // Tạo secrets và deploy PostgreSQL
                sh """
                    kubectl create secret generic postgres-secret \
                        --from-literal=POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
                        --dry-run=client -o yaml | kubectl apply -f -
                        
                    kubectl create secret generic jwt-secret \
                        --from-literal=JWT_SECRET=$JWT_SECRET \
                        --dry-run=client -o yaml | kubectl apply -f -
                        
                    kubectl apply -f k8s/postgres.yaml
                """
            }
        }
        
        stage('Deploy Application') {
            steps {
                // Deploy ứng dụng chính
                sh """
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl set image deployment/music-app music-app=$DOCKER_IMAGE:$DOCKER_TAG
                """
            }
        }
        
        stage('Deploy Monitoring') {
            steps {
                // Deploy Prometheus và Grafana
                sh """
                    kubectl apply -f k8s/prometheus.yaml
                    kubectl apply -f k8s/grafana.yaml
                """
                
                // Verify deployments
                sh '''
                    kubectl rollout status deployment/prometheus
                    kubectl rollout status deployment/grafana
                '''
            }
        }
        
        stage('Deploy Logging') {
            steps {
                // Deploy Fluentd
                sh """
                    kubectl apply -f k8s/fluentd.yaml
                """
                
                // Verify daemonset
                sh 'kubectl rollout status daemonset/fluentd'
            }
        }
        
        stage('Integration Tests') {
            steps {
                // Đợi ứng dụng sẵn sàng
                sh 'kubectl rollout status deployment/music-app'
                
                // Chạy integration tests
                sh '''
                    pip install pytest requests
                    pytest app/tests/test_integration.py
                '''
            }
        }
    }
    
    post {
        success {
            // Notify when success
            slackSend (
                color: '#00FF00',
                message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
            )
        }
        failure {
            // Notify when failed
            slackSend (
                color: '#FF0000',
                message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
            )
            
            // Rollback nếu cần
            sh '''
                kubectl rollout undo deployment/music-app
            '''
        }
        always {
            // Clean up
            sh '''
                docker rmi $DOCKER_IMAGE:$DOCKER_TAG
                docker rmi $DOCKER_IMAGE:latest
            '''
            
            // Archive artifacts
            archiveArtifacts artifacts: 'test-results/**, coverage.xml', fingerprint: true
        }
    }
}