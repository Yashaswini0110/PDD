pipeline {
    agent any

    environment {
        PROJECT_ID   = 'productdesigndev'        // <-- put real project id
        REGION       = 'us-central1'
        REPO_NAME    = 'clauseclear'
        SERVICE_NAME = 'clauseclear-backend'
        IMAGE        = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                // list files at repo root so we see Dockerfile, app.py, etc.
                sh 'ls'
            }
        }

        stage('Build & Sanity Test') {
            steps {
                // quick Python syntax check (not required but nice)
                sh 'python -m compileall . || true'
            }
        }

        stage('Docker Build') {
            steps {
                // build Docker image using Dockerfile at repo root
                sh 'docker build -t ${IMAGE}:latest .'
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
