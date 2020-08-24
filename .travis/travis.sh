#! /bin/bash

# This script will run for a pull request or will run locally if the argument
# 'local' is provided
# if [ ! $PULL_REQUEST_HEAD ] && [ ! "$@" = "local" ]; then
#   exit 0;
# fi

source .env  # Load non-secret enviroment variables e.g. $STAGING_URL

# if [[ "$@" = "local" ]]; then
#   TRAVIS_BRANCH=master
# fi
# 
echo "PULL_REQUEST_BASE: $PULL_REQUEST_BASE";
echo "PULL_REQUEST_HEAD: $PULL_REQUEST_HEAD";

echo "where am I???"
echo "$(git status)"

# Added files in requests directory
REQUEST_FILES=$(git diff --diff-filter=A --name-only $TARGET_BRANCH | cat | grep "^requests\/[^\/]*$")
# REQUEST_FILES=$(git diff --diff-filter=A --name-only $TRAVIS_BRANCH | cat | grep "^requests\/[^\/]*$")

# Altered files in tool directories (eg. galaxy-aust-staging) written to by jenkins
JENKINS_CONTROLLED_FILES=$(git diff --name-only $TARGET_BRANCH | cat  | grep "^(?:\$STAGING_TOOL_DIR\/|PRODUCTION_TOOL_DIR\/).*/")
# JENKINS_CONTROLLED_FILES=$(git diff --name-only $TRAVIS_BRANCH | cat  | grep "^(?:\$STAGING_TOOL_DIR\/|PRODUCTION_TOOL_DIR\/).*/")

if [ $JENKINS_CONTROLLED_FILES ]; then
  echo "Files within $PRODUCTION_TOOL_DIR or $STAGING_TOOL_DIR are written by Jenkins and cannot be altered";
  exit 1;
fi

if [ ! "$REQUEST_FILES" ]; then
  echo "No changed files in requests directory: there are no tests for this scenario";
  exit 0;
fi

# # set up the virtual environment now that we are not using travis
# virtualenv -p python3 .ci
# . .ci/bin/activate
# pip install -r requirements.text

# pass the requests file paths to a python script that checks the input files
python .travis/check_files.py -f $REQUEST_FILES --staging_url $STAGING_URL --production_url $PRODUCTION_URL --staging_dir $STAGING_TOOL_DIR --production_dir $PRODUCTION_TOOL_DIR
