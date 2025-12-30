pipeline {
    agent any

    environment {
        PROJECT_ID   = 'productdesigndev'        // GCP project ID
        REGION       = 'us-central1'             // Region
        REPO_NAME    = 'clauseclear'             // Artifact Registry repo name
        SERVICE_NAME = 'clauseclear-backend'     // Cloud Run service name

        IMAGE        = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage('Docker Build') {
            steps {
                script {
                   echo "Building Docker image..."
                   sh "docker build -t ${IMAGE}:${env.BUILD_NUMBER} -t ${IMAGE}:latest ."
                }
            }
        }

        stage('Push to Artifact Registry') {
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-json', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                        gcloud config set project ${PROJECT_ID}
                        gcloud auth configure-docker ${REGION}-docker.pkg.dev -q
                        docker push ${IMAGE}:${env.BUILD_NUMBER}
                        docker push ${IMAGE}:latest
                    '''
                }
            }
        }

        stage('Deploy to Cloud Run') {
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-json', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                        gcloud config set project ${PROJECT_ID}
                        gcloud config set run/region ${REGION}
                        gcloud run deploy ${SERVICE_NAME} \
                          --image ${IMAGE}:${env.BUILD_NUMBER} \
                          --region ${REGION} \
                          --platform managed \
                          --allow-unauthenticated \
                          --port 5055 \
                          --memory 1Gi \
                          --cpu 1
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}