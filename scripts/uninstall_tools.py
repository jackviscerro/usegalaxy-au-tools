import argparse

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.toolshed import ToolShedClient

"""
Uninstall tools from a galaxy instance via the API using the bioblend package.
This can be used to uninstall any galaxy toolshed tool.  The main use case is
when a tool has been installed incorrectly or when an error has occurred during
installation causing the tool to be partially installed.
"""


def main():
    parser = argparse.ArgumentParser(description='Uninstall tool from a galaxy instance')
    parser.add_argument('-g', '--galaxy_url', help='Galaxy server URL', required=True, dest='galaxy_url')
    parser.add_argument('-a', '--api_key', help='API key for galaxy server', required=True, dest='api_key')
    parser.add_argument(
        '-n',
        '--names',
        help='Names of tools to uninstall.  These can include revision hashes e.g. --names name1@revision1 name1@revision2 name2 ',
        nargs='+',
        required=True,
        dest='names',
    )
    parser.add_argument(
        '-f',
        '--force',
        help='If there are several toolshed entries for one name or name/revision entry uninstall all of them',
        action='store_true',
        dest='force',
    )
    #
    args = parser.parse_args()
    # if not args.names:
    #     raise Exception('Arguments --names (-n) must be provided.')

    uninstall_tools(galaxy_url, api_key, names, force)
    # uninstall_tools(args.galaxy_url, args.api_key, args.names, args.force)


def uninstall_tools(galaxy_server, api_key, names, force):
    tools_to_uninstall = []
    galaxy_instance = GalaxyInstance(url=galaxy_server, key=api_key)
    toolshed_client = ToolShedClient(galaxy_instance)
    installed_tools = [t for t in toolshed_client.get_repositories() if t['status'] != 'Uninstalled']

    for name in names:
        revision = None
        if '@' in name:
            (name, revision) = name.split('@')
        matching_tools = [t for t in installed_tools if (
            t['name'] == name and (not revision or revision == t['changeset_revision'])
        )]
        id_string = 'name %s revision %s' % (name, revision) if revision else 'name %s' % name
        if len(matching_tools) == 0:
            print('*** Warning: No tool with %s' % id_string)
        elif len(matching_tools) > 1 and not force:
            print(
                '*** Warning: More than one toolshed tool found for %s.  ' % id_string
                + 'Not uninstalling any of these tools.  Run script with --force (-f) flag to uninstall anyway'
            )
        else:  # Either there is only one matching tool for the name and revision, or there are many and force=True
            tools_to_uninstall.extend(matching_tools)

    for tool in tools_to_uninstall:
        try:
            print('Uninstalling %s at revision %s' % (tool['name'], tool['changeset_revision']))
            return_value = toolshed_client.uninstall_repository_revision(
                name=tool['name'],
                owner=tool['owner'],
                changeset_revision=tool['changeset_revision'],
                tool_shed_url=tool['tool_shed'],
            )
            print(return_value)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
