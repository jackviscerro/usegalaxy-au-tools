import csv
import arrow
import sys
import argparse

default_tool_shed = 'toolshed.g2.bx.psu.edu'
date_format = 'ddd DD MMM HH:mm:ss ZZZ YYYY'

log_file = 'automated_tool_installation_log.tsv'
dates_file = 'report_dates.txt'
default_days = 7


"""
Generate a report of weekly installations and updates on Galaxy Australia
Because this script runs at the end of the update cron job and the length
of the job may vary, we need to include only installations completed between
now and the time that this script was run last week
"""

argparser = argparse.ArgumentParser(description='Generate report from installation log')
argparser.add_argument('-l', '--use_latest_report_date', action='store_true')


def get_report_header(date):
    return (
        '---\n'
        'site: freiburg\n'
        'title: \'Galaxy Australia tool updates %s\'\n'
        'tags: [tools]\n'
        'supporters:\n'
        '    - galaxytrainingnetwork\n'
        '    - galaxyproject\n'
        '    - galaxyaustralia\n'
        '    - melbinfo\n'
        '    - qcif\n'
        '---\n\n' % date.strftime('%Y-%m-%d')
    )


def get_previous_week_end(week_end):
    try:
        with open(dates_file) as dates:
            lines = dates.readlines()
            return(arrow.get(lines[-1].strip()))
    except Exception:  # maybe the file does not exist or look like we expect
        return week_end.shift(days=-7)


def time_window_satisfied(time_str,  week_begin, week_end):
    time = arrow.get(time_str, date_format)
    if time < week_end and time > week_begin:
        return True
    return False


def main():
    updated_tools = {}
    week_end = arrow.now()
    week_begin = get_previous_week_end(week_end)

    with open(log_file) as tsvfile:
        reader = csv.DictReader(tsvfile, dialect='excel-tab')
        for row in reader:
            label = row['Section Label'].strip()
            if row['Status'] == 'Installed' or (row['Status'] == 'Already Installed' and row['Name'] == 'prokka'):
            # if row['Status'] == 'Installed' and time_window_satisfied(row['Date (UTC)'], week_begin, week_end):
                if not label == 'None':
                    if label not in updated_tools.keys():
                        updated_tools[label] = []
                    updated_tools[label].append(row)

    if not updated_tools.keys():  # nothing to report
        sys.stderr.write('No tools installed this week.\n')
        return

    with open('%s_tool_updates.md' % week_end.strftime('%Y-%m-%d'), 'w') as report:
        report.write(get_report_header(week_end))
        report.write('The following tools have been updated on Galaxy Australia\n\n')
        for key in sorted(updated_tools.keys()):
            report.write('### %s\n\n' % key)
            for item in updated_tools[key]:
                shed_url = item['Tool Shed URL'] or default_tool_shed
                link = 'https://%s/view/%s/%s/%s' % (shed_url.strip(), item['Owner'].strip(), item['Name'], item['Installed Revision'])
                report.write(' - %s was updated to [%s](%s)\n' % (item['Name'], item['Installed Revision'], link))
            report.write('\n')

    with open(dates_file, 'a') as dates:
        dates.write('%s' % str(week_end))


if __name__ == "__main__":
    main()
