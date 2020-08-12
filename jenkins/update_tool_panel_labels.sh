#! /bin/bash
source .env
DISPLAY_NEW_DAYS='21'
DISPLAY_UPDATED_DAYS='21'
REMOTE_USER='galaxy'
DIR_PRODUCTION=/mnt/galaxy-app/config
DIR_STAGING=/mnt/galaxy/galaxy-app/config

FILE=shed_tool_conf.xml_copy_20200811

# python scripts/update_tool_panel_labels.py \
#   --display_new_days $DISPLAY_NEW_DAYS \
#   --display_updated_days $DISPLAY_UPDATED_DAYS \
#   --remote_user $REMOTE_USER \
#   --galaxy_url $PRODUCTION_URL \
#   --remote_dir $DIR_PRODUCTION \
#   -k '/Users/catherine/.ssh/jenkins_bot' # just for testing, do not commit this
  
FILE=shed_tool_conf.xml_copy_CB_20200812

python scripts/update_tool_panel_labels.py \
  --display_new_days $DISPLAY_NEW_DAYS \
  --display_updated_days $DISPLAY_UPDATED_DAYS \
  --remote_user $REMOTE_USER \
  --galaxy_url $STAGING_URL \
  --remote_dir $DIR_STAGING \
  --file $FILE \
  -k '/Users/catherine/.ssh/jenkins_bot' # just for testing, do not commit this