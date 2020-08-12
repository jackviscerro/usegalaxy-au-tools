import argparse
import os
import arrow
# import datetime

from galaxy.util.tool_shed.xml_util import parse_xml
from galaxy.util import xml_to_string

from utils import (
    load_log,
    get_remote_file,
    copy_file_to_remote_location,
    get_toolshed_tools,
)

from pytz import timezone

date_format = 'DD/MM/YY HH:mm:ss'
arrow_parsable_date_format = 'YYYY-MM-DD HH:mm:ss'
aest = timezone('Australia/Queensland')

# import galaxy_util
new_label = 'New'
updated_label = 'Updated'


def main():
    parser = argparse.ArgumentParser(description='Update list of tools with html output that can be viewed in galaxy')
    parser.add_argument('-g', '--galaxy_url', help='Galaxy server URL', required=True)
    parser.add_argument('-d', '--remote_dir', help='File directory on galaxy', required=True)
    parser.add_argument('-u', '--remote_user', help='Remote user', default='galaxy')
    parser.add_argument('-f', '--file', help='File name on galaxy', default='shed_tool_conf.xml_copy_20200811')
    parser.add_argument('-k', '--key_path', help='Path to private ssh key file')
    parser.add_argument('--display_new_days', type=int, help='Number of days to display label for new tool', required=True)
    parser.add_argument('--display_updated_days', type=int, help='Number of days to display label for updated tool', required=True)
    args = parser.parse_args()

    file = args.file
    galaxy_url = args.galaxy_url
    display_new_days = args.display_new_days
    display_updated_days = args.display_updated_days
    
    # print('is int?')
    # print(isinstance(display_new_days, int))
    # return

    copy_args = {
        'file': file,
        'remote_user': args.remote_user,
        'url': galaxy_url.split('//')[1] if galaxy_url.startswith('https://') else galaxy_url,
        'remote_file_path': os.path.join(args.remote_dir, file),
        'key_path': args.key_path,
    }

    def in_time_window(time_str, days):
        converted_datetime = arrow.get(time_str, date_format).format(arrow_parsable_date_format)
        return arrow.get(converted_datetime, tzinfo=aest) > arrow.now().shift(days=-days)
        # time = arrow.get(time_str, date_format, aest)
        # if time > arrow.now().shift(days=-days):
        #     return True
        # return False

    def filter_new(row):
        return row['Status'] == 'Installed' and in_time_window(row['Date (AEST)'], display_new_days) and row['New Tool'] == 'True'

    def filter_updated(row):
        return row['Status'] == 'Installed' and in_time_window(row['Date (AEST)'], display_updated_days) and row['New Tool'] == 'False'

    new_tool_ids = []
    updated_tool_ids = []

    toolshed_tools = get_toolshed_tools(galaxy_url)

    for row in load_log(filter_function=filter_new):
        tool_ids = [t['id'] for t in toolshed_tools if (
            t['tool_shed_repository']['name'] == row['Name']
            and t['tool_shed_repository']['owner'] == row['Owner']
            and t['tool_shed_repository']['changeset_revision'] == row['Installed Revision']
        )]
        new_tool_ids.extend(tool_ids)
    
    for row in load_log(filter_function=filter_updated):
        tool_ids = [t['id'] for t in toolshed_tools if (
            t['tool_shed_repository']['name'] == row['Name']
            and t['tool_shed_repository']['owner'] == row['Owner']
            and t['tool_shed_repository']['changeset_revision'] == row['Installed Revision']
        )]
        updated_tool_ids.extend(tool_ids)

    try:
        get_remote_file(**copy_args)
    except Exception as e:
        print(e)
        raise Exception('Failed to fetch remote file')

    tree, error_message = parse_xml(copy_args['file'])
    root = tree.getroot()
    for section in root:
        if section.tag == 'section':
            for tool in section.getchildren():
                # print(tool)
                if tool.tag == 'tool':
                    tool_id = tool.find('id').text
                    # print(tool_id)
                    # clear labels
                    tool.attrib.pop('labels', None)
                    if tool_id in new_tool_ids:
                        tool.set('labels', new_label)
                    elif tool_id in updated_tool_ids:
                        tool.set('labels', updated_label)
                    # could incorporate maintaining hidden status here
                    # could also be applying a 'deprecated' label

    with open('test_xml_out_7', 'w') as handle:
        handle.write(xml_to_string(root, pretty=True))
            

if __name__ == "__main__":
    main()