import argparse
import yaml


def tool_from_url(url, section_label=None):
    if url.startswith('https://'):
        url = url.strip('/').split('//')[1]
    tool_shed_url, _, owner, name, revision = url.split('/')
    tool = {
        'name': name,
        'owner': owner,
        'revisions': [revision],
        'tool_shed_url': tool_shed_url,
        'tool_panel_section_label': '?'
    }
    if section_label:
        tool.update({'tool_panel_section_label': section_label})
    return tool


def main():
    parser = argparse.ArgumentParser(description='Convert toolshed links to shed-tools format')
    parser.add_argument('-o', '--output_path', help='Output file path')
    parser.add_argument('-f', '--file', help='File containing one toolshed link per line')
    parser.add_argument('-u', '--url', help='Toolshed link')
    parser.add_argument('-s', '--section_label', help='Tool panel section label')

    args = parser.parse_args()
    if args.file and args.url:
        print('Error: --file (-f) and  --url (-u) are mutually exclusive options')

    tools = []
    if args.url:
        tools.append(tool_from_url(args.url, section_label=args.section_label))
    elif args.file:
        with open(args.file) as handle:
            for line in handle.readlines():
                if line.strip():
                    tools.append(tool_from_url(line, section_label=args.section_label))
    
    with open(args.output_path, 'w') as handle:
        yaml.dump({'tools': tools}, handle)


if __name__ == '__main__':
    main()