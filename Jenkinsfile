#!groovy

// Testing pipeline

pipeline {
    agent {
        label 'hamlet-latest'
    }
    options {
        buildDiscarder(
            logRotator(
                numToKeepStr: '10'
            )
        )
        skipDefaultCheckout()
    }

    environment {
        COMPOSE_PROJECT_NAME = 'igl-node-au'
        cd_environment = 'c1'
        slack_channel = '#igl-automatic-messages'
        properties_file = '/var/opt/properties/devnet.properties'
    }

    parameters {
        booleanParam(
            name: 'run_integration_tests',
            defaultValue: false,
            description: 'Run integration tests for all components'
        )
        booleanParam(
            name: 'force_deploy',
            defaultValue: false,
            description: 'Force deployment to start'
        )
    }

    stages {

        stage('Testing') {

            stages {

                stage('Setup') {
                    steps {
                        dir('test/intergov/') {
                            script{
                                def repo = checkout scm
                                env.GIT_COMMIT = repo
                            }

                            sh '''#!/bin/bash
                                touch docker/node.igl-node-au-local.env
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
                        dir('test/intergov/')  {
                            sh '''#!/bin/bash
                                python3.6 pie.py intergov.tests.unit
                            '''

                            sh '''#!/bin/bash
                                python3.6 pie.py intergov.tests.integration
                            '''
                        }
                    }
                }
            }

            post {
                always {
                    dir('test/intergov/'){
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
                    dir('test/intergov/') {
                        sh '''#!/bin/bash
                            if [[ -f pie.py ]]; then
                                python3.6 pie.py intergov.destroy
                            fi
                        '''
                    }
                }
            }
        }

        stage('Artefact')  {
            when {
                anyOf {
                    equals expected: true, actual: params.force_deploy
                    allOf {
                        branch 'master'
                    }
                }
            }

            stages {

                stage ('Setup' ) {
                    steps {
                        dir('artefact/') {
                            script{
                                def repo = checkout scm
                                env.GIT_COMMIT = repo.GIT_COMMIT
                            }
                        }

                        script {
                            def productProperties = readProperties interpolate: true, file: "${properties_file}" ;
                            productProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                    }
                }

                // Intergov - API Lambdas
                stage('API Build') {

                    steps {

                        dir('artefact/serverless') {
                            sh '''#!/bin/bash
                                if [[ -d "${HOME}/.nodenv" ]]; then
                                    export PATH="$HOME/.nodenv/bin:$PATH"
                                    eval "$(nodenv init - )"
                                    nodenv install 12.16.1 || true
                                    nodenv shell 12.16.1
                                fi

                                npm ci

                                npx sls package --package dist/document_api      --config "apis/document_api/serverless.yml"
                                npx sls package --package dist/message_api       --config "apis/message_api/serverless.yml"
                                npx sls package --package dist/message_rx_api    --config "apis/message_rx_api/serverless.yml"
                                npx sls package --package dist/subscriptions_api --config "apis/subscriptions_api/serverless.yml"
                            '''
                        }
                    }

                    post {
                        success {
                            dir('artefact/serverless') {
                                archiveArtifacts artifacts: 'dist/document_api/document_api.zip', fingerprint: true
                                archiveArtifacts artifacts: 'dist/message_api/message_api.zip', fingerprint: true
                                archiveArtifacts artifacts: 'dist/message_rx_api/message_rx_api.zip', fingerprint: true
                                archiveArtifacts artifacts: 'dist/subscriptions_api/subscriptions_api.zip', fingerprint: true
                            }
                        }
                    }
                }

                stage('ImageUpload - document_api - lambda ') {
                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'document-api-imp'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/'
                        BUILD_SRC_DIR = ''
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'lambda'
                    }

                    steps {

                        dir('artefact/serverless') {
                            sh '''
                                mkdir -p ${WORKSPACE}/artefact/dist/
                                cp dist/document_api/document_api.zip ${WORKSPACE}/artefact/dist/lambda.zip
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                        ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                        ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                stage('ImageUpload - message_api - lambda') {
                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'message-api-imp'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/'
                        BUILD_SRC_DIR = ''
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'lambda'
                    }

                    steps {

                        dir('artefact/serverless') {
                            sh '''
                                mkdir -p ${WORKSPACE}/artefact/dist/
                                cp dist/message_api/message_api.zip ${WORKSPACE}/artefact/dist/lambda.zip
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                        ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                        ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                stage('ImageUpload - message_rx_api - lambda') {
                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'messagerx-api-imp'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/'
                        BUILD_SRC_DIR = ''
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'lambda'
                    }

                    steps {

                        dir('artefact/serverless') {
                            sh '''
                                mkdir -p ${WORKSPACE}/artefact/dist/
                                cp dist/message_rx_api/message_rx_api.zip ${WORKSPACE}/artefact/dist/lambda.zip
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                        ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                        ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                stage('ImageUpload - subscriptions_api - lambda') {
                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'subscriptions-api-imp'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/'
                        BUILD_SRC_DIR = ''
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'lambda'
                    }

                    steps {

                        dir('artefact/serverless') {
                            sh '''
                                mkdir -p ${WORKSPACE}/artefact/dist/
                                cp dist/subscriptions_api/subscriptions_api.zip ${WORKSPACE}/artefact/dist/lambda.zip
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                        ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                        ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }


                // Intergov - API Gateways
                stage('artefact - document_api - gw') {

                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'document-api'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/intergov/apis/document'
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'openapi'
                    }

                    steps {

                        dir('artefact/intergov/apis/document') {
                             sh '''#!/bin/bash
                                # Workaround for missing api spec
                                if [[ ! -f swagger.yaml ]]; then
                                    cp ../../../serverless/apis/swagger.yaml ./
                                fi

                                npm install --no-save swagger-cli

                                npx swagger-cli bundle --dereference --outfile openapi-extended-base.json --type json swagger.yaml
                                npx swagger-cli validate openapi-extended-base.json

                                mkdir -p dist/
                                zip -j "dist/openapi.zip" "openapi-extended-base.json"
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                            ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                            ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                stage('artefact - message_api - gw') {

                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'message-api'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/intergov/apis/message'
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'openapi'
                    }

                    steps {

                        dir('artefact/intergov/apis/message') {
                            sh '''#!/bin/bash
                                # Workaround for missing api spec
                                if [[ ! -f swagger.yaml ]]; then
                                    cp ../../../serverless/apis/swagger.yaml ./
                                fi

                                npm install --no-save swagger-cli

                                npx swagger-cli bundle --dereference --outfile openapi-extended-base.json --type json swagger.yaml
                                npx swagger-cli validate openapi-extended-base.json

                                mkdir -p dist/
                                zip -j "dist/openapi.zip" "openapi-extended-base.json"
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                            ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                            ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }


                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                stage('artefact - message_rx_api - gw') {

                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'messagerx-api'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/intergov/apis/message_rx'
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'openapi'
                    }

                    steps {

                        dir('artefact/intergov/apis/message_rx') {
                            sh '''#!/bin/bash
                                # Workaround for missing api spec
                                if [[ ! -f swagger.yaml ]]; then
                                    cp ../../../serverless/apis/swagger.yaml ./
                                fi

                                npm install --no-save swagger-cli

                                npx swagger-cli bundle --dereference --outfile openapi-extended-base.json --type json swagger.yaml
                                npx swagger-cli validate openapi-extended-base.json

                                mkdir -p dist/
                                zip -j "dist/openapi.zip" "openapi-extended-base.json"
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                            ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                            ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }


                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                stage('artefact - subscriptions_api - gw') {

                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS = 'subscriptions-api'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/intergov/apis/subscriptions'
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'openapi'
                    }

                    steps {

                        dir('artefact/intergov/apis/subscriptions') {
                            sh '''#!/bin/bash
                                # Workaround for missing api spec
                                if [[ ! -f swagger.yaml ]]; then
                                    cp ../../../serverless/apis/swagger.yaml ./
                                fi

                                npm install --no-save swagger-cli

                                npx swagger-cli bundle --dereference --outfile openapi-extended-base.json --type json swagger.yaml
                                npx swagger-cli validate openapi-extended-base.json

                                mkdir -p dist/
                                zip -j "dist/openapi.zip" "openapi-extended-base.json"
                            '''
                        }

                        // Product Setup
                        sh '''#!/bin/bash
                            ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                            ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }


                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

                // Intergov - Processors
                stage('artefact - Intergov - processor') {

                    environment {
                        //hamlet deployment variables
                        DEPLOYMENT_UNITS =  'proc-msg,proc-msgupdater,proc-callbdel,proc-callbspd,proc-rejstat,proc-docspider,proc-channelrouter,proc-channelpoller,proc-subhandler,proc-chnmsgret'
                        SEGMENT = 'intergov'
                        BUILD_PATH = 'artefact/'
                        DOCKER_CONTEXT_DIR = 'artefact/'
                        BUILD_SRC_DIR = ''
                        DOCKER_FILE = 'artefact/docker/node.Dockerfile'
                        GENERATION_CONTEXT_DEFINED = ''

                        image_format = 'docker'
                    }

                    steps {
                        // Product Setup
                        sh '''#!/bin/bash
                            ${AUTOMATION_BASE_DIR}/setContext.sh || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        sh '''#!/bin/bash
                            ${AUTOMATION_DIR}/manageImages.sh -g "${GIT_COMMIT}" -f "${image_format}"  || exit $?
                        '''

                        script {
                            def contextProperties = readProperties interpolate: true, file: "${WORKSPACE}/context.properties";
                            contextProperties.each{ k, v -> env["${k}"] ="${v}" }
                        }

                        build job: "../../deploy/deploy-${env["cd_environment"]}", wait: false, parameters: [
                                extendedChoice(name: 'DEPLOYMENT_UNITS', value: "${env.DEPLOYMENT_UNITS}"),
                                string(name: 'GIT_COMMIT', value: "${env.GIT_COMMIT}"),
                                booleanParam(name: 'AUTODEPLOY', value: true),
                                string(name: 'IMAGE_FORMATS', value: "${env.image_format}"),
                                string(name: 'SEGMENT', value: "${env.SEGMENT}")
                        ]
                    }

                }

            }

            post {
                success {
                    slackSend (
                        message: "*Success* | <${BUILD_URL}|${JOB_NAME}> \n intergov artefact complete",
                        channel: "${env["slack_channel"]}",
                        color: "#50C878"
                    )
                }

                failure {
                    slackSend (
                        message: "*Failure* | <${BUILD_URL}|${JOB_NAME}> \n intergov artefact failed",
                        channel: "${env["slack_channel"]}",
                        color: "#B22222"
                    )
                }
            }
        }
    }
}
