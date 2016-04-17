from datetime import date, timedelta

import arrow
from flask import Blueprint, jsonify, request
import requests

from backup import backup_completed_tasks
from common import require_secret, dashboard_item
from config import config
import secrets

module = Blueprint(config['module_name'], __name__)

def get_number_tasks_completed_today():
    url = 'http://api.todoist.com/API/getProductivityStats?token=%s' % secrets.TODOIST_AUTH_TOKEN
    result = requests.get(url).json()
    return result['days_items'][0]['total_completed']

def get_completed(limit=50, offset=0):
    url = 'https://todoist.com/API/v6/get_all_completed_items?token=%s&limit=%s&offset=%s' % (secrets.TODOIST_AUTH_TOKEN, limit, offset)
    result = requests.get(url).json()
    return result['items']

def get_tasks_date_range(start, end=None, limit=None):
    url = 'https://todoist.com/API/v6/get_all_completed_items?token=%s&to_date=%sT07:00' % (secrets.TODOIST_AUTH_TOKEN, start)
    if end:
        url += '&from_date=%sT07:00' % end
    if limit:
        url += '&limit=%s' % limit
    result = requests.get(url).json()
    return result['items']

def get_tasks_completed_today():
    today = date.today()
    return get_tasks_date_range(today)

def create_dashboard_item_for_query(tasks_completed, query, title=None):
    complete = any(s['content'] == query for s in tasks_completed)
    return {
        'title': title if title else query,
        'body': 'Complete' if complete else 'Incomplete',
        'color': '#CAE2B0' if complete else '#FFCC80'
    }

def first_where(tasks, query):
    return next((s for s in tasks if s['content'] == query), False)

@module.route('/backup')
@module.route('/backup/')
@require_secret
def backup_completed_tasks():
    return jsonify(backup_completed_tasks(uploader))

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

@module.route('/today')
@module.route('/today/')
@require_secret
def tasks_completed_today_route():
    tasks_completed = get_tasks_completed_today()
    return jsonify({
        'count': len(tasks_completed),
        'items': tasks_completed
    })

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
            'color': 'papayawhip' if task else '#EBAD99'
        })
    return dashboard_item(items)
