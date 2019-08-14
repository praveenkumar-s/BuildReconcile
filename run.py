import jenkins
import json
from pprint import pprint
import LoadDB
import sqlite3
import time
from progress.bar import ShadyBar
from datetime import datetime, timedelta
import csv
import sys
import notifications


def key_except(dict, key):
    try:
        return dict[key]
    except:
        return None


def get_job_list_from_server(server):
    server = jenkins.Jenkins(server)
    jobs = server.get_all_jobs()
    return jobs


def apply_filter(jobs, filter='inclusion'):
    filters = json.load(open('filters.json', 'r'))
    filtered_jobs = []
    for items in jobs:
        if(key_except(items, 'color') != 'disabled'):
            if(filter == 'inclusion'):
                if(items['name'] in filters['inclusion']['job_names']):
                    filtered_jobs.append(items)
            else:
                if(items['name'] not in filters['exclusion']['job_names']):
                    filtered_jobs.append(items)
    return filtered_jobs


def verify_build_on_filtered_jobs(filtered_jobs, server):
    server = jenkins.Jenkins(server)
    conn = sqlite3.connect("local.db")
    untracked_builds = []
    flight_plan = json.load(open('flight_plan.json'))
    job_depth = flight_plan['job_depth']
    days_before = flight_plan['consider_builds_before_days']
    for things in filtered_jobs:
        try:
            builds = server.get_job_info(things['name'])['builds'][:job_depth]
            for build in builds:
                build_info = server.get_build_info(
                    things['name'], build['number'])
                # --------------build processing-------------------------
                display_name = build_info['displayName']
                build_status = build_info['result']
                epoch = build_info['timestamp']
                url = build_info['url']
                cur = conn.execute("select count(*) from data where Build_Number = ? and Build_Completed>= ? or Build_Link = ?",
                                   (display_name, time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(epoch/1000.)), url))
                if(cur.fetchall()[0][0] >= 1 or (datetime.utcfromtimestamp(epoch/1000.) < datetime.utcnow() - timedelta(days=days_before))):
                    pass
                else:
                    untracked_builds.append(build_info)
                # -------------------------------------------------------
        except:
            print("Exception During Build Processing",
                  sys.exc_info()[0], things['url'])
    conn.close()
    return untracked_builds


if __name__ == "__main__":
    start = datetime.now()
    lost_builds = []
    flight_plan = json.load(open('flight_plan.json'))
    servers = flight_plan['servers']
    filter_type = flight_plan['filters']
    serverBar = ShadyBar('Servers', max=servers.__len__())
    # do operation for each jenkins server
    for server in servers:
        if(LoadDB.create_local_db()):
            jobs = get_job_list_from_server(server)
            # TODO: Filter exclusion logic
            filtered_jobs = apply_filter(jobs, filter=filter_type)
            lost_builds.extend(
                verify_build_on_filtered_jobs(filtered_jobs, server))
        else:
            print("Failure to load cache")
        serverBar.next()

    json.dump(lost_builds, open('untracked.json', 'w+'))

    csv_data = [['Build_Name', 'Built_On_VM', 'Url',
                 'Build_Status', 'Time_stamp', 'Full_name']]
    for items in lost_builds:
        try:
            row = [
                items['displayName'],
                items['builtOn'],
                items['url'],
                items['result'],
                time.strftime('%Y-%m-%d %H:%M:%S',
                              time.gmtime(items['timestamp']/1000.)),
                items['fullDisplayName']
            ]
            csv_data.append(row)
        except:
            print("Error while building report", sys.exc_info()[0], str(items))

    with open('untracked.csv', 'w+', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(csv_data)
    csvFile.close()
    fp = open('message_template.txt')
    body =fp.read()
    fp.close()
    body = body.format(
        str((datetime.now()-start).seconds)+' seconds',
        str(lost_builds.__len__()),
        ' , '.join(servers),
        filter_type,
        str(flight_plan['consider_builds_before_days'])
    )
    if(lost_builds.__len__() == 0):
        notifications.perform_send_mail(mailing_list='mailing_list_2', attachment_file_path=None,
                                        subject="Tracking Missed SCM Build jobs", body=body)
    else:
        notifications.perform_send_mail(mailing_list='mailing_list_1', attachment_file_path='untracked.csv',
                                        subject="Tracking Missed SCM Build jobs", body=body)
