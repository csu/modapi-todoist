from flask import Blueprint, jsonify
import requests

from common import require_secret
from config import config
import secrets

module = Blueprint(config['module_name'], __name__)

def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

@module.route('/backup')
@module.route('/backup/')
@require_secret
def backup_completed_tasks():
    base_url = 'https://todoist.com/API/v6/get_all_completed_items?token=%s' % secrets.TODOIST_AUTH_TOKEN

    projects = {}
    items = []

    limit = 50
    offset = 0
    while (offset == 0) or result['items']:
        url = '%s&limit=%s&offset=%s' % (base_url, limit, offset)
        result = requests.get(url).json()
        items += result['items']
        projects = merge_dicts(projects, result['projects'])
        offset += limit

    uploader.quick_upload({'items': items, 'projects': projects},
        file_prefix='todoist', folder=secrets.BACKUP_FOLDER_ID)

    return jsonify({
        'status': 'ok',
        'items': len(items),
        'projects': len(projects)
    })

def get_tasks_completed_today():
    url = 'http://api.todoist.com/API/getProductivityStats?token=%s' % secrets.TODOIST_AUTH_TOKEN
    result = requests.get(url).json()
    return result['days_items'][0]['total_completed']

@module.route('/today/dashboard')
@module.route('/today/dashboard/')
@require_secret
def tasks_completed_today_dashboard():
    count = get_tasks_completed_today()

    colors = ['#EBAD99', '#FFCC66', '#CCFF66']
    color = colors[0]
    if count >= 3:
        color = colors[1]
    if count >= 5:
        color = colors[2]

    return jsonify({'items': [{
        'title': 'Tasks Completed',
        'body': count,
        'color': color
    }]})