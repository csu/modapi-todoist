import datetime
import json
import tempfile

from flask import Blueprint, jsonify
import requests

from common import require_secret
from config import config
import secrets

module = Blueprint(config['module_name'], __name__)

@module.route('/backup')
@module.route('/backup/')
@require_secret
def backup_completed_tasks():


    temp_file = tempfile.NamedTemporaryFile()
    temp_file.write(json.dumps(checkins))

    filename = 'foursquare-%s.json' % datetime.date.today()
    folder = secrets.BACKUP_FOLDER_ID
    uploader.upload(temp_file.name, title=filename, parent=folder)

    temp_file.close()

    return jsonify({'status': 'ok'})