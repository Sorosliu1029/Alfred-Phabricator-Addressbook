#!/usr/bin/python
# encoding: utf-8

import sys
from urllib import urlencode
import argparse
from workflow import Workflow, web, ICON_WEB, ICON_WARNING, ICON_USER, PasswordNotFound


def get_addressbook(token):
    url = 'http://ph.in.ruguoapp.com/api/phriction.document.search'
    data = {
        'constraints[ids][0]': 14,
        'attachments[content]': 1,
        'api.token': token,
    }
    payload = urlencode(data)
    headers = { 'Content-Type': "application/x-www-form-urlencoded" }
    res = web.post(url, data=payload, headers=headers)
    res.raise_for_status()
    result = res.json()
    return result['result']['data'][0]['attachments']['content']['content']['raw']

def extract_data(raw_content):
    result = []
    for line in raw_content.splitlines():
        line = line.strip('|')
        fields = map(unicode.strip, line.split('|'))
        if len(fields) > 3:
            result.append(
                dict(zip(['id', 'name', 'phone', 'birthday', 'email', 'job', 'jkid'], fields))
            )

    return result[1:]

def search_key(staff):
    email_entity = staff['email'].split('@')[0]
    elements = [staff['name'], staff['jkid'], email_entity]
    return u' '.join(elements)
            

def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('--setkey', dest='token', nargs='?', default=None)
    parser.add_argument('query', nargs='?', default=None)
    args = parser.parse_args(wf.args)

    if args.token:
        wf.save_password('phabricator', args.token)
        return 0

    try:
        token = wf.get_password('phabricator')
    except PasswordNotFound:
        wf.add_item(
            title='No token set',
            subtitle='Please use jktoken to set your Phabricator token',
            valid=False,
            icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    query = args.query

    def wrapper():
        raw_content = get_addressbook(token)
        return extract_data(raw_content)
    
    staffs = wf.cached_data('staffs', wrapper, max_age=60*60)

    if query:
        staffs = wf.filter(query, staffs, key=search_key, min_score=20)

    if not staffs:
        wf.add_item('No staff found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for jiker in staffs:
        wf.add_item(
            title=jiker['name'] + u' / ' + jiker['jkid'],
            subtitle=jiker['email'],
            largetext=jiker['job'],
            copytext=jiker['email'],
            valid=True, 
            icon=ICON_USER)

    wf.send_feedback()

if __name__ == '__main__':
    wf = Workflow()

    sys.exit(wf.run(main))