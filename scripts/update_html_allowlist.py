import argparse
import os

from utils import (
    load_log,
    get_remote_file,
    copy_file_to_remote_location,
    get_toolshed_tools,
)


def main():
    parser = argparse.ArgumentParser(description='Update list of tools with html output that can be viewed in galaxy')
    parser.add_argument('-g', '--galaxy_url', help='Galaxy server URL', required=True)
    parser.add_argument('-p', '--remote_file_dir', help='File directory on galaxy', required=True)
    parser.add_argument('-u', '--remote_user', help='Remote user', default='galaxy')
    parser.add_argument('-f', '--file', help='File name on galaxy', default='sanitize_whitelist.txt')

    parser.add_argument('-k', '--key_path', help='Path to private ssh key file')
    args = parser.parse_args()

    file = args.file
    galaxy_url = args.galaxy_url

    copy_args = {
        'file': file,
        'remote_user': args.remote_user,
        'url': galaxy_url.split('//')[1] if galaxy_url.startswith('https://') else galaxy_url,
        'remote_file_path': os.path.join(args.remote_file_dir, file),
        'key_path': args.key_path,
    }

    try:
        get_remote_file(**copy_args)
    except Exception as e:
        print(e)
        raise Exception('Failed to fetch remote file')

    with open(file) as handle:
        listed_tool_ids = [l.strip() for l in handle.readlines() if l.strip()]
        listed_tools_no_versions = {get_deversioned_id(t) for t in listed_tool_ids if not is_comment(t)}

    new_allowed_tool_ids = []
    toolshed_tools = get_toolshed_tools(galaxy_url)
    log_table = load_log()
    for row in log_table:
        tool_ids = [t['id'] for t in toolshed_tools if (
            t['tool_shed_repository']['name'] == row['Name']
            and t['tool_shed_repository']['owner'] == row['Owner']
            and t['tool_shed_repository']['changeset_revision'] == row['Installed Revision']
        )]
        for tool_id in tool_ids:
            if get_deversioned_id(tool_id) in listed_tools_no_versions and tool_id not in listed_tool_ids:
                new_allowed_tool_ids.append(tool_id)

    with open(file, 'w') as handle:
        for tool_id in listed_tool_ids + new_allowed_tool_ids:
            handle.write(tool_id + '\n')

    try:
        copy_file_to_remote_location(**copy_args)
    except Exception as e:
        print(e)
        raise Exception('Failed to copy file to galaxy')


def is_comment(line):
    return line.strip().startswith('#')


def get_deversioned_id(tool_id):
    return '/'.join(tool_id.split('/')[:-1])


if __name__ == "__main__":
    main()
