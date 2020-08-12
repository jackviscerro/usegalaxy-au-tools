#! /bin/bash
source .env

FILE=sanitize_whitelist.txt
DIR_PRODUCTION=/mnt/galaxy-app/config
DIR_STAGING=/mnt/galaxy/galaxy-app/config
USER=galaxy

python scripts/update_html_allowlist --file $FILE --galaxy_url $PRODUCTION_URL --remote_dir $DIR_PRODUCTION --remote_user $USER
python scripts/update_html_allowlist --file $FILE --galaxy_url $PRODUCTION_URL --remote_dir $DIR_STAGING --remote_user $USER
