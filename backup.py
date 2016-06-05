import requests

import secrets

def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

def backup_completed_tasks(uploader):
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

    return {
        'status': 'ok',
        'items': len(items),
        'projects': len(projects)
    }

if __name__ == '__main__':
    from ...uploader import gdrive
    backup_completed_tasks(gdrive.GDriveUploader())