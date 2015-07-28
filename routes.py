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