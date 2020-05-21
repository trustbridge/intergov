#!groovy

// Testing pipeline

pipeline {
    agent {
        label 'hamlet-latest'
    }
    options {
        timestamps ()
        buildDiscarder(
            logRotator(
                numToKeepStr: '10'
            )
        )
        disableConcurrentBuilds()
        durabilityHint('PERFORMANCE_OPTIMIZED')
        parallelsAlwaysFailFast()
        skipDefaultCheckout()
    }

    environment {
        DOCKER_BUILD_DIR = "${env.DOCKER_STAGE_DIR}/${BUILD_TAG}"
    }

    parameters {
        booleanParam(
            name: 'run_integration_tests',
            defaultValue: false,
            description: 'Run integration tests for all components'
        )
    }

    stages {

        stage('Setup') {
            steps {
                dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {
                    script{
                        def repoIntergov = checkout scm
                        env.GIT_COMMIT = repoIntergov.GIT_COMMIT
                    }
                }
            }
        }


        stage('Testing') {

            stages {
                stage('Setup') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {
                            sh '''#!/bin/bash
                                export COMPOSE_PROJECT_NAME=au
                                cp demo-au.env demo-au-local.env
                                python3.6 pie.py intergov.build
                                python3.6 pie.py intergov.start
                                echo "waiting for startup"
                                sleep 60s
                            '''
                        }
                    }
                }

                stage('Run Testing - Unit') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/intergov/")  {
                            sh '''#!/bin/bash
                                export COMPOSE_PROJECT_NAME=au
                                python3.6 pie.py intergov.tests.unit
                            '''
                        }
                    }
                }

                stage('Run Testing - Integration') {
                    when {
                        anyOf {
                            changeRequest()
                            equals expected: true, actual: params.run_integration_tests
                        }
                    }


                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/intergov/")  {
                            sh '''#!/bin/bash
                                export COMPOSE_PROJECT_NAME=au
                                python3.6 pie.py intergov.tests.integration
                            '''
                        }
                    }
                }
            }

            post {
                always {
                    dir("${env.DOCKER_BUILD_DIR}/test/intergov/"){
                        publishHTML(
                            [
                                allowMissing: true,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Intergov Coverage Report',
                                reportTitles: ''
                            ]
                        )
                    }
                }
                cleanup {
                    dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {
                        sh '''#!/bin/bash
                            if [[ -f pie.py ]]; then
                                export COMPOSE_PROJECT_NAME=au
                                python3.6 pie.py intergov.destroy
                            fi
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                if ( env.BRANCH_NAME == 'master' ) {
                    build job: '../cotp-devnet/build-intergov/master', parameters: [
                        string(name: 'branchref_intergov', value: "${env.GIT_COMMIT}")
                    ]
                }
            }
        }

        failure {
            slackSend (
                message: "Testing Failed - ${JOB_NAME} (<${BUILD_URL}|Open>)\n Intergov Testing Failed \n Branch: ${BRANCH_NAME} \n PR: (<${CHANGE_URL}> | ${CHANGE_ID} - ${CHANGE_TITLE}>",
                channel: "#igl-automatic-messages",
                color: "#B22222"
            )
        }

        cleanup {
            cleanWs()
        }
    }
}
