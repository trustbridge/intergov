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
            name: 'all_tests',
            defaultValue: false,
            description: 'Run tests for all components'
        )
    }

    stages {
        // intergov required for running full test suite
        stage('Testing') {

            when {
                anyOf {
                    changeRequest()
                    equals expected: true, actual: params.all_tests
                }
            }


            stages {
                stage('Setup') {
                    when {
                        changeRequest()
                    }

                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {

                            checkout scm

                            sh '''#!/bin/bash
                                cp demo-local-example.env demo-local.env
                                python3.6 pie.py intergov.build
                                python3.6 pie.py intergov.start
                                echo "waiting for startup"
                                sleep 60s
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/intergov/")  {
                            sh '''#!/bin/bash
                                python3.6 pie.py intergov.tests.unit
                                python3.6 pie.py intergov.tests.integration || true
                            '''
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
                    }
                }
            }

            post {
                cleanup {
                    dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {
                        sh '''#!/bin/bash
                            if [[ -f pie.py ]]; then
                                python3.6 pie.py intergov.destroy
                            fi
                        '''
                    }
                }
            }
        }
    }

    post {
        cleanup {
            cleanWs()
        }
    }
}
