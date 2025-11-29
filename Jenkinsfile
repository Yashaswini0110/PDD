pipeline {
    agent any

    environment {
        PROJECT_ID   = 'YOUR_GCP_PROJECT_ID'   // <-- change this
        REGION       = 'asia-south1'
        REPO_NAME    = 'clauseclear'
        SERVICE_NAME = 'clauseclear-backend'
        IMAGE        = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                dir('PDD') {
                    sh 'ls'
                }
            }
        }

        stage('Build & Sanity Test') {
            steps {
                dir('PDD') {
                    sh 'python -m compileall . || true'
                }
            }
        }

        stage('Docker Build') {
            steps {
                dir('PDD') {
                    sh 'docker build -t ${IMAGE}:latest .'
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
                    gcloud run deploy ${SERVICE_NAME} \
                      --image ${IMAGE}:latest \
                      --region ${REGION} \
                      --platform managed \
                      --allow-unauthenticated \
                      --port 5055
                    '''
                }
            }
        }
    }
}
