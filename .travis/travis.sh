#! /bin/bash

# This script will run for a pull request or will run locally if the argument
# 'local' is provided
if [ ! $TRAVIS_PULL_REQUEST ] && [ ! "$@" = "local" ]; then
  exit 0;
fi

export $(cat .env)  # Load non-secret enviroment variables e.g. $STAGING_URL

if [[ "$@" = "local" ]]; then
  TRAVIS_BRANCH=master
  export $(cat .secret.env)  # secret API keys
fi

echo "TRAVIS_BRANCH: $TRAVIS_BRANCH";
echo "TRAVIS_PULL_REQUEST_BRANCH: $TRAVIS_PULL_REQUEST_BRANCH";

# Added files in requests directory
REQUEST_FILES=$(git diff --diff-filter=A --name-only $TRAVIS_BRANCH | cat | grep "^requests\/[^\/]*$")

# Altered files in tool directories (eg. galaxy-aust-staging) written to by jenkins
JENKINS_CONTROLLED_FILES=$(git diff --name-only $TRAVIS_BRANCH | cat  | grep "^(?:\$STAGING_TOOL_DIR\/|PRODUCTION_TOOL_DIR\/).*/")

if [ $JENKINS_CONTROLLED_FILES ]; then
  echo "Files within $PRODUCTION_TOOL_DIR or $STAGING_TOOL_DIR are written by Jenkins and cannot be altered";
  exit 1;
fi

if [ ! "$REQUEST_FILES" ]; then
  echo "No changed files in requests directory: there are no tests for this scenario";
  exit 0;
fi

# pass the requests file paths to a python script that checks the input files
python .travis/check_files.py -f $REQUEST_FILES --staging_url $STAGING_URL --staging_api_key $STAGING_API_KEY --production_url $PRODUCTION_URL --production_api_key $PRODUCTION_API_KEY
