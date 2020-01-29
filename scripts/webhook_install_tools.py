# from bioblend.galaxy import GalaxyInstance
# from bioblend.galaxy.toolshed import ToolShedClient
import argparse
import yaml
import os
import sys
import re
from uninstall_tools import uninstall_tools


INSTALL_LOG = 'tmp/install_log.txt'


def main():
    parser = argparse.ArgumentParser(description='Python version of bash script')
    parser.add_argument('-f', '--files', help='Tool input files', nargs='+')
    parser.add_argument('-b', '--build_number', help='Jenkins build number')
    parser.add_argument('-i', '--install_id', help='Install ID')
    parser.add_argument('-u', '--staging_url', help='Galaxy staging server URL')
    parser.add_argument('-k', '--staging_api_key', help='API key for galaxy staging server')
    parser.add_argument('-g', '--production_url', help='Galaxy production server URL')
    parser.add_argument('-a', '--production_api_key', help='API key for galaxy production server')
    # parser.add_argument(
    #     '-n',
    #     '--names',
    #     help='Names of tools to uninstall.  These can include revision hashes e.g. --names name1@revision1 name1@revision2 name2 ',
    #     nargs='+',
    # )
    # parser.add_argument(
    #     '-f',
    #     '--force',
    #     help='If there are several toolshed entries for one name or name/revision entry uninstall all of them',
    #     action='store_true',
    # )

    args = parser.parse_args()
    # galaxy_url = args.galaxy_url
    # api_key = args.api_key
    # names = args.names
    # force = args.force
    files = args.files
    staging_url = args.staging_url
    staging_api_key = args.staging_api_key
    production_url = args.production_url
    production_api_key = args.production_api_key

    log('AAAAAAAAAA')
    print_preamble()  # write the variables blah
    tools = get_tools(files)
    print(tools)
    for tool in tools:
        sys.stderr.write('Installing %s on %s' % (tool['name'], staging_url))
        install_result = install_tool(
            url=staging_url,
            server='staging',
            api_key=staging_api_key,
            tool=tool
        )
        if install_result['halt']:
            log_entry(install_result, tool)


def log(text=None, newlines=1):
    if text:
        sys.stderr.write(text)
    sys.stderr.write('\n' * newlines)


def shed_tools_args(tool):  # could replace this with --yaml-tool option
    str = '--name %s --owner %s --section_label \'%s\'' % (tool['name'], tool['owner'], tool['tool_panel_section_label'])
    if tool['revisions']:
        str += ' --revisions %s' % ' '.join(tool['revisions'])
    if tool['tool_shed_url']:
        str += ' --toolshed %s' % tool['tool_shed_url']
    return str


def verify_shed_tools_installation(log_path):
    # actually just read the output and decide whether it has been installed
    # the assumption is that only one tool has been fed to shed_tools
    # TODO capture error message when there is one
    # TODO capture the phrase 'already installed'
    status_name_version_pattern = re.compile(
        "(\w+) repositories \(1\): \[\('([^']+)',\s*u?'(\w+)'\)\]",
        # "(\w+) repositories \(1\): \[\('([^']+)',\s*u'(\w+)'\)\]",
        re.MULTILINE,
    )
    with open(log_path) as logfile:
        matches = status_name_version_pattern.findall(logfile.read())
    if len(matches) == 1:
        [match] = matches
        return {
            'status': match[0].lower(),
            'name': match[1],
            'revision': match[2],
        }


def install_tool(server, url, api_key, tool):
    log('HELLO')
    step = server.title()
    os.system('rm -f %s ||:;' % INSTALL_LOG)  # Delete log file if it already exists
    command = 'shed-tools install %s -g %s -a %s -v --log_file %s' % (shed_tools_args(tool), url, api_key, INSTALL_LOG)
    log(command)
    os.system(command)
    with open(INSTALL_LOG) as install_log:
        install_output = install_log.read()
        log('****')
        log(install_output)
    result = verify_shed_tools_installation(INSTALL_LOG)
    if result:
        installation_status = result['status']
        installed_name = result['name']
        installed_revision = ['revision']
    else:
        log('Error: unable to verify shed-tools installation')
        log('%d matches found for search pattern' % len(matches))
        # get out, log row etc

    if tool['name'] != installed_name:
        # get out, log row etc
        pass
    if installation_status == 'errored':
        log('Installation error.  Uninstalling on %s', url)
        # log_row(status=status, step=step, tool=tool)
        uninstall_tool(url, api_key, '%s@%s' % (installed_name, installed_revision))
        if server == 'production':
            uninstall_tool(staging_url, staging_api_key, '%s@%s' % (installed_name, installed_revision))
        # get out, log row etc
        # return {'status': status, 'continue': False}

    elif installation_status == 'skipped':
        log('Package appears to be already installed on %s' % url)
    elif installation_status == 'installed':
        log('%s has been installed on %s' % (installed_name, url))
    # log_row(status=status, step=step, tool=tool, installed_revision=installed_revision)
    return {
        'status': installation_status,
        'halt': installation_status == 'errored',
        'error_log': install_output if installation_status == 'errored' else None,
        'step': step,
        'installed_revision': installed_revision,
    }

    }

    def log_row(status, step, tool, installed_revision, tests_passed_staging=None, tests_passed_production=None)

      # if [ ! "$INSTALLATION_STATUS" ] || [ ! "$INSTALLED_NAME" ] || [ ! "$INSTALLED_REVISION" ]; then
      #   # TODO what if this is production server?  wind back staging installation?
      #   log_row "Script error"
      #   exit_installation 1 "Could not verify installation from shed-tools output."
      #   return 1
      # fi
      # if [ ! "$TOOL_NAME" = "$INSTALLED_NAME" ]; then
      #   # If these are not the same name it is probably due to this script.
      #   # uninstall and abandon process with 'Script error'
      #   python scripts/uninstall_tools.py -g $URL -a $API_KEY -n $INSTALLED_NAME;
      #   log_row "Script Error"
      #   exit_installation 1 "Unexpected value for name of installed tool.  Expecting "$TOOL_NAME", received $INSTALLED_NAME";
      #   return 1
      # fi
      # # INSTALLATION_STATUS can have one of 3 values: Installed, Skipped, Errored
      # if [ $INSTALLATION_STATUS = "Errored" ]; then
      #   # The tool may or may not be installed according to the API, so it needs to be
      #   # uninstalled with bioblend
      #   echo "Installation error.  Uninstalling $TOOL_NAME on $URL";
      #   python scripts/uninstall_tools.py -g $URL -a $API_KEY -n "$INSTALLED_NAME@$INSTALLED_REVISION";
      #   if [ $SERVER = "PRODUCTION" ]; then
      #     # also uninstall on staging
      #     echo "Uninstalling $TOOL_NAME on $STAGING_URL";
      #     python scripts/uninstall_tools.py -g $STAGING_URL -a $STAGING_API_KEY -n $INSTALLED_NAME;
      #   fi
      #   log_row $INSTALLATION_STATUS
      #   echo -e "Failed to install $TOOL_NAME on $URL (status $INSTALLATION_STATUS)\n" >> $ERROR_LOG
      #   cat $INSTALL_LOG >> $ERROR_LOG; echo -e "\n\n" >> $ERROR_LOG;
      #   exit_installation 1 ""
      #   return 1;
      #
      # elif [ $INSTALLATION_STATUS = "Skipped" ]; then
      #   # The linting process should prevent this scenario if the tool is installed on production
      #   # If the tool is installed on staging, skip testing
      #   echo "Package appears to be already installed on $URL";
      #
      # elif [ $INSTALLATION_STATUS = "Installed" ]; then
      #   echo "$TOOL_NAME has been installed on $URL";
      #
      # else
      #   log_row "Script error"
      #   exit_installation 1 "Could not verify installation from shed-tools output."
      #   return 1
      # fi



def print_preamble():
    pass


def get_tools(files):
    print(files)
    tools_by_entry = []
    tools = []
    for file in files:
        with open(file) as input:
            content = yaml.safe_load(input.read())['tools']
            if isinstance(content, list):
                tools_by_entry += content
            else:
                tools_by_entry.append(content)

    for tool in tools_by_entry:
        if 'revisions' in tool.keys() and len(tool['revisions']) > 1:
            for rev in tool['revisions']:
                new_tool = tool.copy()
                new_tool['revisions'] = [rev]
            tools.append(new_tool)
        else:
            tools.append(tool.copy())

    return tools


if __name__ == "__main__": main()
