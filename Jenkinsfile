pipeline {
    agent any

    environment {
        PROJECT_ID   = 'productdesigndev'        // GCP project ID
        REGION       = 'us-central1'             // Region
        REPO_NAME    = 'clauseclear'             // Artifact Registry repo name
        SERVICE_NAME = 'clauseclear-backend'     // Cloud Run service name

        IMAGE        = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
        
        GCP_CREDENTIALS_ID = 'gcp-sa-json'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE}:latest ."
                script {
                    echo "✓ Docker image built successfully: ${IMAGE}:latest"
                }
            }
        }

        stage('Local Test') {
            steps {
                script {
                    echo "Running basic container health check..."
                    sh '''
                        # Start container in background with dynamic port binding
                        CONTAINER_ID=$(docker run -d -p 0:5055 ${IMAGE}:latest)
                        echo "Container started with ID: $CONTAINER_ID"
                        
                        # Wait for container to be ready
                        sleep 8
                        
                        # Get dynamically assigned host port and trim whitespace
                        PORT_MAPPING=$(docker port $CONTAINER_ID 5055/tcp)
                        HOST_PORT=$(echo $PORT_MAPPING | cut -d: -f2 | tr -d '[:space:]')
                        echo "Container is accessible on host port: $HOST_PORT"
                        
                        # Build health check URL to avoid tokenization issues
                        HEALTH_URL="http://localhost:${HOST_PORT}/health"
                        echo "Health check URL: ${HEALTH_URL}"
                        
                        # Test health endpoint using variable (prevents shell tokenization bugs)
                        if curl -f "${HEALTH_URL}" 2>/dev/null; then
                            echo "✓ Health check passed"
                        else
                            echo "⚠ Health check failed or endpoint not available"
                            docker logs $CONTAINER_ID
                            exit 1
                        fi
                        
                        # Cleanup
                        docker stop $CONTAINER_ID
                        docker rm $CONTAINER_ID
                        echo "✓ Container cleaned up"
                    '''
                }
            }
        }

        stage('Push to Artifact Registry') {
            steps {
                script {
                    try {
                        withCredentials([
                            file(credentialsId: env.GCP_CREDENTIALS_ID, variable: 'GOOGLE_APPLICATION_CREDENTIALS'),
                            string(credentialsId: 'gemini-api-key', variable: 'GEMINI_API_KEY')
                        ]) {
                            echo "✓ Required credentials validated: GCP service account and GEMINI_API_KEY"
                            sh '''
                                echo "Authenticating with GCP service account..."
                                gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                                gcloud config set project ${PROJECT_ID}
                                echo "Configuring Docker for Artifact Registry..."
                                gcloud auth configure-docker ${REGION}-docker.pkg.dev -q
                                echo "Pushing image to Artifact Registry..."
                                docker push ${IMAGE}:latest
                                echo "✓ Image pushed successfully to ${IMAGE}:latest"
                            '''
                        }
                    } catch (org.jenkinsci.plugins.credentialsbinding.impl.CredentialNotFoundException e) {
                        error("Required credentials not found: ${e.getMessage()}. Please configure 'gcp-sa-json' and 'gemini-api-key' credentials")
                    } catch (Exception e) {
                        error("Failed to push to Artifact Registry: ${e.getMessage()}")
                    }
                }
            }
        }

        stage('Deploy to Cloud Run') {
            steps {
                script {
                    try {
                        // Collect required and optional credentials
                        def credentialsList = [
                            file(credentialsId: env.GCP_CREDENTIALS_ID, variable: 'GOOGLE_APPLICATION_CREDENTIALS'),
                            string(credentialsId: 'gemini-api-key', variable: 'GEMINI_API_KEY')
                        ]
                        
                        // Optional credentials
                        try {
                            credentialsList.add(string(credentialsId: 'mongo-uri', variable: 'MONGO_URI'))
                            echo "✓ MONGO_URI credential found (optional)"
                        } catch (Exception e) {
                            echo "⚠ MONGO_URI credential not found (optional, continuing without it)"
                        }
                        
                        // Optional Firebase credentials
                        def firebaseVars = []
                        try {
                            credentialsList.add(string(credentialsId: 'firebase-api-key', variable: 'FIREBASE_API_KEY'))
                            firebaseVars.add('FIREBASE_API_KEY')
                        } catch (Exception e) {
                            echo "⚠ FIREBASE_API_KEY credential not found (optional)"
                        }
                        
                        try {
                            credentialsList.add(string(credentialsId: 'firebase-auth-domain', variable: 'FIREBASE_AUTH_DOMAIN'))
                            firebaseVars.add('FIREBASE_AUTH_DOMAIN')
                        } catch (Exception e) {
                            echo "⚠ FIREBASE_AUTH_DOMAIN credential not found (optional)"
                        }
                        
                        try {
                            credentialsList.add(string(credentialsId: 'firebase-project-id', variable: 'FIREBASE_PROJECT_ID'))
                            firebaseVars.add('FIREBASE_PROJECT_ID')
                        } catch (Exception e) {
                            echo "⚠ FIREBASE_PROJECT_ID credential not found (optional)"
                        }
                        
                        try {
                            credentialsList.add(string(credentialsId: 'firebase-messaging-sender-id', variable: 'FIREBASE_MESSAGING_SENDER_ID'))
                            firebaseVars.add('FIREBASE_MESSAGING_SENDER_ID')
                        } catch (Exception e) {
                            echo "⚠ FIREBASE_MESSAGING_SENDER_ID credential not found (optional)"
                        }
                        
                        try {
                            credentialsList.add(string(credentialsId: 'firebase-app-id', variable: 'FIREBASE_APP_ID'))
                            firebaseVars.add('FIREBASE_APP_ID')
                        } catch (Exception e) {
                            echo "⚠ FIREBASE_APP_ID credential not found (optional)"
                        }
                        
                        withCredentials(credentialsList) {
                            sh '''
                                echo "Authenticating with GCP service account..."
                                gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                                gcloud config set project ${PROJECT_ID}
                                gcloud config set run/region ${REGION}
                                
                                # Build environment variables for Cloud Run
                                ENV_VARS="--set-env-vars GEMINI_MODEL_NAME=gemini-2.0-flash"
                                
                                # Required: GEMINI_API_KEY
                                ENV_VARS="$ENV_VARS --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY"
                                echo "✓ GEMINI_API_KEY will be set in Cloud Run"
                                
                                # Optional: MONGO_URI
                                if [ -n "$MONGO_URI" ]; then
                                    ENV_VARS="$ENV_VARS --set-env-vars MONGO_URI=$MONGO_URI"
                                    echo "✓ MONGO_URI will be set in Cloud Run"
                                fi
                                
                                # Optional: Firebase env vars
                                if [ -n "$FIREBASE_API_KEY" ]; then
                                    ENV_VARS="$ENV_VARS --set-env-vars FIREBASE_API_KEY=$FIREBASE_API_KEY"
                                    echo "✓ FIREBASE_API_KEY will be set in Cloud Run"
                                fi
                                if [ -n "$FIREBASE_AUTH_DOMAIN" ]; then
                                    ENV_VARS="$ENV_VARS --set-env-vars FIREBASE_AUTH_DOMAIN=$FIREBASE_AUTH_DOMAIN"
                                    echo "✓ FIREBASE_AUTH_DOMAIN will be set in Cloud Run"
                                fi
                                if [ -n "$FIREBASE_PROJECT_ID" ]; then
                                    ENV_VARS="$ENV_VARS --set-env-vars FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
                                    echo "✓ FIREBASE_PROJECT_ID will be set in Cloud Run"
                                fi
                                if [ -n "$FIREBASE_MESSAGING_SENDER_ID" ]; then
                                    ENV_VARS="$ENV_VARS --set-env-vars FIREBASE_MESSAGING_SENDER_ID=$FIREBASE_MESSAGING_SENDER_ID"
                                    echo "✓ FIREBASE_MESSAGING_SENDER_ID will be set in Cloud Run"
                                fi
                                if [ -n "$FIREBASE_APP_ID" ]; then
                                    ENV_VARS="$ENV_VARS --set-env-vars FIREBASE_APP_ID=$FIREBASE_APP_ID"
                                    echo "✓ FIREBASE_APP_ID will be set in Cloud Run"
                                fi
                                
                                echo "Deploying to Cloud Run..."
                                gcloud run deploy ${SERVICE_NAME} \
                                  --image ${IMAGE}:latest \
                                  --region ${REGION} \
                                  --platform managed \
                                  --allow-unauthenticated \
                                  $ENV_VARS
                                
                                echo "✓ Deployment completed successfully"
                                
                                # Get and display the service URL
                                SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
                                echo "========================================"
                                echo "🚀 Service deployed at: $SERVICE_URL"
                                echo "========================================"
                                echo "Test endpoints:"
                                echo "  - Frontend: $SERVICE_URL/static/index.html"
                                echo "  - Health: $SERVICE_URL/health"
                                echo "  - API Docs: $SERVICE_URL/docs"
                                echo "========================================"
                            '''
                        }
                    } catch (Exception e) {
                        error("Failed to deploy to Cloud Run: ${e.getMessage()}")
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "✓ Pipeline completed successfully!"
        }
        failure {
            echo "✗ Pipeline failed. Check logs above for details."
        }
        always {
            echo "Pipeline execution completed."
        }
    }
}