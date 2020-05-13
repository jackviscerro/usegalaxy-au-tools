#! /bin/bash
chmod +x jenkins/install_tools.sh

source jenkins/config; # variables BASE_LOG_DIR VENV_PATH

MODE="$1"; # Two modes possible: "install" for tool request, "update" for cron update
if [ ! "$MODE" = "install" ] && [ ! "$MODE" = "update" ]; then
  echo "First positional argument to jenkins/main must be install or update"
  exit 1
fi

BASH_V="$(echo ${BASH_VERSION} | head -c 1)" # this will be "4" if the bash version is 4.x, empty otherwise

# FORCE means skip tool tests (1=true, 0=false).  This can be switched on by
# including the text [FORCE] a pull request title.  This is not recommended in
# the first instance of installing a tool and should only be used after initial
# tool test results have been reviewed
FORCE=0
GIT_COMMIT_MESSAGE=$(git log --format=%B -n 1 $GIT_COMMIT | cat)
[[ $GIT_COMMIT_MESSAGE == *"[FORCE]"* ]] && FORCE=1

# A .secret.env file is useful when running locally for storing API keys
# that would otherwise be encrypted in jenkins.  If a .secret.env file is
# present, LOCAL_ENV is set to 1 (true)
SECRET_ENV_FILE=".secret.env"
[ -f $SECRET_ENV_FILE ] && LOCAL_ENV=1 || LOCAL_ENV=0

if [ $LOCAL_ENV = 1 ]; then
    echo "Script running in local enviroment";
    # GIT_COMMIT and GIT_PREVIOUS_COMMIT are supplied by Jenkins
    # Use HEAD and HEAD~1 when running locally
    BUILD_NUMBER="local_$(date '+%Y%m%d%H%M%S')"
    GIT_PREVIOUS_COMMIT=HEAD~1;
    GIT_COMMIT=HEAD;
    BASE_LOG_DIR="logs"
    # When running script outside jenkins enviroment arguments after
    # 'install' or 'update' are parsed as request
    # file paths, e.g. bash jenkins/main.sh my_tool.yml
    ARGS=( "$@" )
    LOCAL_REQUEST_FILES=$(echo "${ARGS[@]:1}" | xargs)
else
    echo "Script running on jenkins server";
fi

LOG_DIR=${BASE_LOG_DIR}/${MODE}_build_${BUILD_NUMBER}

export LOCAL_ENV
export BUILD_NUMBER
export LOG_FILE="${LOG_DIR}/install_log.txt"
export GIT_COMMIT
export GIT_PREVIOUS_COMMIT
export LOG_DIR
export BASH_V
export MODE
export FORCE

activate_virtualenv() {
  # Activate the virtual environment on jenkins. If this script is being run for
  # the first time we will need to set up the virtual environment
  # The venv is set up in Jenkins' home directory so that we do not have
  # to rebuild it each time and multiple jobs can share it
  # VENV_PATH="/var/lib/jenkins/jobs_common"
  [ $LOCAL_ENV = 1 ] && VENV_PATH=".."
  VIRTUALENV="${VENV_PATH}/.venv3"
  REQUIREMENTS_FILE="jenkins/requirements.yml"
  CACHED_REQUIREMENTS_FILE="${VIRTUALENV}/cached_requirements.yml"

  [ ! -d $VENV_PATH ] && mkdir $VENV_PATH
  [ ! -d $VIRTUALENV ] && virtualenv -p python3 $VIRTUALENV
  # shellcheck source=../.venv3/bin/activate
  . "$VIRTUALENV/bin/activate"

  # if requirements change, reinstall requirements
  [ ! -f $CACHED_REQUIREMENTS_FILE ] && touch $CACHED_REQUIREMENTS_FILE
  if [ "$(diff $REQUIREMENTS_FILE $CACHED_REQUIREMENTS_FILE)" ]; then
    pip install -r $REQUIREMENTS_FILE
    cp $REQUIREMENTS_FILE $CACHED_REQUIREMENTS_FILE
  fi
}

if [ $MODE = "install" ]; then
  # First check whether changed files are in the path of tool requests, that is within the requests folder but not within
  # any subfolders of requests.  If so, we run the install script.  If not we exit.
  REQUEST_FILES=$(git diff --name-only --diff-filter=A $GIT_PREVIOUS_COMMIT $GIT_COMMIT | grep "^requests\/[^\/]*$" | xargs)

  if [ $LOCAL_ENV = 1 ] && [[ "$LOCAL_REQUEST_FILES" ]]; then
    REQUEST_FILES="$LOCAL_REQUEST_FILES"
  fi

  export REQUEST_FILES

  if [[ ! $REQUEST_FILES ]]; then
    # Exit early and do not write a log if the commit does not contain request files
    echo "No added files in requests folder, no tool installation required"
    exit 0;
  else
    echo "Tools from the following files will be installed"
    echo $REQUEST_FILES;
  fi
fi

# Create log folder structure
[ -d $LOG_DIR ] || mkdir -p $LOG_DIR
mkdir -p $LOG_DIR/staging;  # staging test json output
mkdir -p $LOG_DIR/production;  # production test json output
mkdir -p $LOG_DIR/planemo;  # planemo html output tools that fail tests

activate_virtualenv
echo "Saving output to $LOG_FILE"
bash jenkins/install_tools.sh 2>&1 | tee $LOG_FILE
