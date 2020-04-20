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
    }

    stages {
        stage('Run Testing') {
            steps {
                build(
                    job: '../testnet-deploy/master',
                    parameters: [ string(name: 'branchref_intergov', value: "${GIT_COMMIT}") ]
                )
            }
        }
    }
}
