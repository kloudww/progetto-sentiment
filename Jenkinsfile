pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    triggers {
        githubPush()
    }

    environment {
        NOME_IMMAGINE = 'sentiment-api'
        DESTINATARIO = 'team@example.com'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'docker build --target test -t ${NOME_IMMAGINE}-test:${BUILD_NUMBER} .'
                sh 'docker build --target produzione -t ${NOME_IMMAGINE}:${BUILD_NUMBER} .'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    rm -rf report
                    esito=0
                    docker run --name test-${BUILD_NUMBER} ${NOME_IMMAGINE}-test:${BUILD_NUMBER} || esito=$?
                    docker cp test-${BUILD_NUMBER}:/app/report ./report || true
                    docker rm test-${BUILD_NUMBER}
                    exit $esito
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'report/risultati.xml'
                }
            }
        }

        stage('Deploy') {
            when {
                expression { (env.GIT_BRANCH ?: env.BRANCH_NAME ?: '') ==~ /(origin\/)?main/ }
            }
            steps {
                sh 'docker tag ${NOME_IMMAGINE}:${BUILD_NUMBER} ${NOME_IMMAGINE}:latest'
                sh 'docker compose build prometheus grafana'
                sh 'docker compose up -d --no-build'
                sh '''
                    for tentativo in $(seq 1 30); do
                        stato=$(docker inspect --format "{{.State.Health.Status}}" sentiment-api)
                        if [ "$stato" = "healthy" ]; then
                            echo "Servizio in salute"
                            exit 0
                        fi
                        sleep 2
                    done
                    echo "Il servizio non risulta in salute"
                    docker logs sentiment-api
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            script { notifica('SUCCESSO') }
        }
        failure {
            script { notifica('FALLITA') }
        }
        cleanup {
            sh 'docker rm -f test-${BUILD_NUMBER} || true'
            sh 'docker image prune -f || true'
        }
    }
}

def notifica(String esito) {
    echo "Pipeline ${env.JOB_NAME} numero ${env.BUILD_NUMBER}: ${esito}"
    try {
        mail to: env.DESTINATARIO,
             subject: "Pipeline ${env.JOB_NAME} numero ${env.BUILD_NUMBER}: ${esito}",
             body: "Dettagli: ${env.BUILD_URL}"
    } catch (Exception errore) {
        echo "Invio email non riuscito: ${errore.message}"
    }
}
