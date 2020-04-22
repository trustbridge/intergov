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
            name: 'run_tests',
            defaultValue: false,
            description: 'Run tests for all components'
        )
    }

    stages {

        stage('Setup') {
            steps {
                dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {
                    checkout scm
                }
            }
        }


        stage('Testing') {

            when {
                anyOf {
                    branch 'master'
                    changeRequest()
                    equals expected: true, actual: params.run_tests
                }
            }


            stages {
                stage('Setup') {
                    when {
                        changeRequest()
                    }

                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/intergov/") {
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
                                python3.6 pie.py intergov.tests.integration
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
        success {
            script {
                if ( env.BRANCH_NAME == 'master' ) {
                    build job: '../cotp-devnet/build/master', parameters: [
                        string(name: 'branchref_intergov', value: "${GIT_COMMIT}")
                    ]
                }
            }
        }

        cleanup {
            cleanWs()
        }
    }
}
