import csv
import subprocess

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.toolshed import ToolShedClient
from bioblend.galaxy.tools import ToolClient
from bioblend.toolshed import ToolShedInstance
from bioblend.toolshed.repositories import ToolShedRepositoryClient


def get_galaxy_instance(url, api_key=None):
    if not url.startswith('https://'):
        url = 'https://' + url
    return GalaxyInstance(url, api_key)


def get_repositories(url, api_key):  # TODO is api key necessary?
    galaxy_instance = GalaxyInstance(url, api_key)
    toolshed_client = ToolShedClient(galaxy_instance)
    return toolshed_client.get_repositories()


def get_toolshed_tools(url):
    galaxy_instance = get_galaxy_instance(url)
    tool_client = ToolClient(galaxy_instance)
    return [tool for tool in tool_client.get_tools() if tool.get('tool_shed_repository')]


def load_log(filter_function=None):
    def filter(row):
        if filter_function is not None:
            return filter_function(row)
        else:
            return True
    log_file = 'automated_tool_installation_log.tsv'
    table = []
    with open(log_file) as tsvfile:
        reader = csv.DictReader(tsvfile, dialect='excel-tab')
        for row in reader:
            if filter(row):
                table.append(row)
    return table


def get_toolshed_repository_client(url):
    if not url.startswith('https://'):
        url = 'https://' + url
    toolshed = ToolShedInstance(url=url)
    return ToolShedRepositoryClient(toolshed)


def get_valid_tools_for_repo(name, owner, revision, tool_shed_url):
    repo_client = get_toolshed_repository_client(tool_shed_url)
    data = repo_client.get_repository_revision_install_info(name, owner, revision)
    repository, metadata, install_info = data
    return metadata.get('valid_tools')


def get_remote_file(file, remote_file_path, url, remote_user, key_path=None):
    # print('file, remote_file_path, url, remote_user, key_path')
    # print(file, remote_file_path, url, remote_user, key_path)
    key_arg = '' if not key_path else '-i %s' % key_path
    # if key_path:
    #     key_arg = '-i %s' % key_path
    command = 'scp %s %s@%s:%s %s' % (key_arg, remote_user, url, remote_file_path, file)
    subprocess.check_output(command, shell=True)


def copy_file_to_remote_location(file, remote_file_path, remote_user, url, key_path=None):
    key_arg = '' if not key_path else '-i %s' % key_path
    # key_arg = ''
    # if key_path:
    #     key_arg = ' -i %s' % key_path
    command = 'scp %s %s %s@%s:%s' % (key_arg, file, remote_user, url, remote_file_path)
    subprocess.check_output(command, shell=True)
