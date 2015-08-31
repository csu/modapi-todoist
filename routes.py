from datetime import date, timedelta

import arrow
from flask import Blueprint, jsonify, request
import requests

from common import require_secret, dashboard_item
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
        # TODO: refactor this to use get_completed
        # fairly simple, but I don't want to risk breaking things for now
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

def get_number_tasks_completed_today():
    url = 'http://api.todoist.com/API/getProductivityStats?token=%s' % secrets.TODOIST_AUTH_TOKEN
    result = requests.get(url).json()
    return result['days_items'][0]['total_completed']

@module.route('/today/dashboard')
@module.route('/today/dashboard/')
@require_secret
def tasks_completed_today_dashboard():
    count = get_number_tasks_completed_today()

    colors = ['#EBAD99', '#FFCC66', '#CAE2B0']
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

def get_completed(limit=50, offset=0):
    url = 'https://todoist.com/API/v6/get_all_completed_items?token=%s&limit=%s&offset=%s' % (secrets.TODOIST_AUTH_TOKEN, limit, offset)
    result = requests.get(url).json()
    return result['items']

def get_tasks_date_range(start, end, limit=50):
    url = 'https://todoist.com/API/v6/get_all_completed_items?token=%s&from_date=%sT07:00&to_date=%sT07:00&limit=%s' % (secrets.TODOIST_AUTH_TOKEN, start, end, limit)
    result = requests.get(url).json()
    return result['items']

def get_tasks_completed_today():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    return get_tasks_date_range(today, tomorrow)

@module.route('/today')
@module.route('/today/')
@require_secret
def tasks_completed_today_route():
    tasks_completed = get_tasks_completed_today()
    return jsonify({
        'count': len(tasks_completed),
        'items': tasks_completed
    })

@module.route('/today/query')
@module.route('/today/query/')
@require_secret
def query_completed_tasks():
    query = request.args.get('query')
    return jsonify({
        'query': query,
        'result': query_today_compelted(query)
    })

def create_dashboard_item_for_query(tasks_completed, query, title=None):
    complete = any(s['content'] == query for s in tasks_completed)
    return {
        'title': title if title else query,
        'body': 'Complete' if complete else 'Incomplete',
        'color': '#CAE2B0' if complete else '#FFCC80'
    }

def first_where(tasks, query):
    return next((s for s in tasks if s['content'] == query), False)

@module.route('/today/query/dashboard')
@module.route('/today/query/dashboard/')
@require_secret
def query_completed_tasks_dashboard():
    queries = request.args.getlist('query')
    tasks_completed = get_tasks_completed_today()
    items = []
    for query in queries:
        title = None
        if '--' in query:
            query_parts = query.split('--')
            query = query_parts[0]
            title = query_parts[1]
        items.append(create_dashboard_item_for_query(tasks_completed, query, title=title))
    return dashboard_item(items)

@module.route('/since/dashboard')
@module.route('/since/dashboard/')
def query_since_completion():
    queries = request.args.getlist('query')
    tasks = get_completed()
    items = []
    for query in queries:
        title = None
        if '--' in query:
            query_parts = query.split('--')
            query = query_parts[0]
            title = query_parts[1]
        task = first_where(tasks, query)
        body = arrow.get(task['completed_date'], 'ddd DD MMM YYYY HH:mm:ss Z').humanize() if task else 'Not found'
        items.append({
            'title': title if title else query,
            'body': body,
            'color': '#CAE2B0' if task else '#FFCC80'
        })
    return dashboard_item(items)
