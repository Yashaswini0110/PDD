pipeline {

    agent any

    environment {
        PROJECT_ID   = 'productdesigndev'
        REGION       = 'us-central1'
        REPO_NAME    = 'clauseclear'
        SERVICE_NAME = 'clauseclear-backend'
        IMAGE        = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage('Build & Sanity Test') {
            steps {
                sh 'echo "Skipping sanity tests inside Jenkins — handled within Docker."'
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE}:latest ."
            }
        }

        stage('Push to Artifact Registry') {
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-json', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh """
                    gcloud auth activate-service-account --key-file=\$GOOGLE_APPLICATION_CREDENTIALS
                    gcloud config set project ${PROJECT_ID}
                    gcloud auth configure-docker ${REGION}-docker.pkg.dev -q
                    docker push ${IMAGE}:latest
                    """
                }
            }
        }

        stage('Deploy to Cloud Run') {
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-json', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh """
                    gcloud auth activate-service-account --key-file=\$GOOGLE_APPLICATION_CREDENTIALS
                    gcloud config set project ${PROJECT_ID}
                    gcloud config set run/region ${REGION}

                    gcloud run deploy ${SERVICE_NAME} \
                        --image ${IMAGE}:latest \
                        --region ${REGION} \
                        --platform managed \
                        --allow-unauthenticated \
                        --port 5055
                    """
                }
            }
        }
    }
}
