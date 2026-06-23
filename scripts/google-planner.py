#!/usr/bin/env python3
"""
Google Planner CLI - Combined Google Calendar and Google Tasks
Commands:
  calendar:
    list       - List events (next 7 days)
    add         - Add event
    delete      - Delete event by ID
    update      - Update event
    search      - Search events
    calendars   - List calendars
  tasks:
    tasks       - List all tasks
    task-add    - Add a new task
    task-done   - Mark task as completed
    task-delete - Delete task
    task-update - Update task
"""

import os
import sys
import json
import pickle
import time
import datetime
import requests
from urllib.parse import urlencode

# ====== Config ======
PROXY = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or \
        os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy') or None
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(SKILL_DIR, '.env')

# 读取 .env 文件
def load_env():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

env_vars = load_env()

CAL_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'gcalcli')
CAL_TOKEN_FILE = os.path.join(CAL_CONFIG_DIR, 'token.pkl')
TASK_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'gtasks')
TASK_TOKEN_FILE = os.path.join(TASK_CONFIG_DIR, 'token.pkl')
CLIENT_ID = env_vars.get('GOOGLE_CLIENT_ID', '')
CLIENT_SECRET = env_vars.get('GOOGLE_CLIENT_SECRET', '')
REDIRECT_URI = 'http://localhost:8080'
CAL_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]
TASK_SCOPES = ['https://www.googleapis.com/auth/tasks']

os.makedirs(CAL_CONFIG_DIR, exist_ok=True)
os.makedirs(TASK_CONFIG_DIR, exist_ok=True)

# 检查凭证
if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: Missing Google OAuth credentials.")
    print("Please create .env file in the skill directory with:")
    print("  GOOGLE_CLIENT_ID=your_client_id")
    print("  GOOGLE_CLIENT_SECRET=your_client_secret")
    sys.exit(1)

# ====== Shared Functions ======
def get_session():
    session = requests.Session()
    if PROXY:
        session.proxies = {
            'http': PROXY,
            'https': PROXY
        }
    return session

def refresh_cal_token(token_data):
    """Refresh calendar token if needed"""
    session = get_session()
    expires_at = token_data.get('expires_at', 0)
    if time.time() >= expires_at - 300:
        print("Calendar token expiring, refreshing...")
        data = {
            'refresh_token': token_data['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
        resp = session.post('https://oauth2.googleapis.com/token', data=data, timeout=30)
        if resp.status_code != 200:
            return None
        new_token = resp.json()
        new_token['refresh_token'] = token_data['refresh_token']
        new_token['expires_at'] = time.time() + new_token.get('expires_in', 3600)
        with open(CAL_TOKEN_FILE, 'wb') as f:
            pickle.dump(new_token, f)
        print("Calendar token refreshed.")
        return new_token
    return token_data

def refresh_task_token(token_data):
    """Refresh task token if needed"""
    session = get_session()
    expires_at = token_data.get('expires_at', 0)
    if time.time() >= expires_at - 300:
        print("Task token expiring, refreshing...")
        data = {
            'refresh_token': token_data['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
        resp = session.post('https://oauth2.googleapis.com/token', data=data, timeout=30)
        if resp.status_code != 200:
            return None
        new_token = resp.json()
        new_token['refresh_token'] = token_data['refresh_token']
        new_token['expires_at'] = time.time() + new_token.get('expires_in', 3600)
        with open(TASK_TOKEN_FILE, 'wb') as f:
            pickle.dump(new_token, f)
        print("Task token refreshed.")
        return new_token
    return token_data

def get_cal_token():
    """Get calendar access token"""
    if not os.path.exists(CAL_TOKEN_FILE):
        print("No calendar token found. Run: python google-planner.py auth")
        sys.exit(1)
    with open(CAL_TOKEN_FILE, 'rb') as f:
        token_data = pickle.load(f)
    token_data = refresh_cal_token(token_data)
    if not token_data:
        sys.exit(1)
    return token_data['access_token']

def get_task_token():
    """Get task access token"""
    if not os.path.exists(TASK_TOKEN_FILE):
        print("No task token found. Run: python google-planner.py auth")
        sys.exit(1)
    with open(TASK_TOKEN_FILE, 'rb') as f:
        token_data = pickle.load(f)
    token_data = refresh_task_token(token_data)
    if not token_data:
        sys.exit(1)
    return token_data['access_token']

# ====== Auth ======
def auth(service=None):
    """Get authorization URL for calendar/tasks/both"""
    if not service or service == 'calendar':
        cal_auth()
    if not service or service == 'tasks':
        task_auth()

def cal_auth():
    """Authenticate calendar"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(CAL_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    print("=" * 60)
    print("Open this URL in your browser to authorize Calendar:")
    print("=" * 60)
    print(url)
    print("=" * 60)

    sys.stdout.write("\nAfter authorizing, paste the 'code' value from the redirect URL here:\n> ")
    sys.stdout.flush()
    code = sys.stdin.readline().strip()

    if not code:
        print("No code provided, aborting.")
        return

    print("\nExchanging code for token...")
    data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    session = get_session()
    resp = session.post('https://oauth2.googleapis.com/token', data=data, timeout=30)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    token_data = resp.json()
    token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
    with open(CAL_TOKEN_FILE, 'wb') as f:
        pickle.dump(token_data, f)
    print(f"Calendar token saved!")

def task_auth():
    """Authenticate tasks"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(TASK_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    print("=" * 60)
    print("Open this URL in your browser to authorize Tasks:")
    print("=" * 60)
    print(url)
    print("=" * 60)

    sys.stdout.write("\nAfter authorizing, paste the 'code' value from the redirect URL here:\n> ")
    sys.stdout.flush()
    code = sys.stdin.readline().strip()

    if not code:
        print("No code provided, aborting.")
        return

    print("\nExchanging code for token...")
    data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    session = get_session()
    resp = session.post('https://oauth2.googleapis.com/token', data=data, timeout=30)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    token_data = resp.json()
    token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
    with open(TASK_TOKEN_FILE, 'wb') as f:
        pickle.dump(token_data, f)
    print(f"Tasks token saved!")

# ====== Calendar Functions ======
def auto_assign_color(summary, description=''):
    """Auto-assign color based on keywords and importance"""
    text = (summary + ' ' + description).lower()

    # 高优先级 - 截止/重要
    if any(kw in text for kw in ['截止', 'deadline', 'ddl', '提交', '重要', '紧急', '必须']):
        return 11  # 番茄红
    # 比赛/黑客松
    elif any(kw in text for kw in ['比赛', '黑客松', 'hackathon', '大赛', '竞赛', '路演']):
        return 6  # 橘色
    # 会议/论坛
    elif any(kw in text for kw in ['会议', 'meeting', '论坛', '分享', '活动', '培训']):
        return 9  # 蓝莓蓝
    # 学习/课程
    elif any(kw in text for kw in ['学习', '课程', '上课', '讲座', '读书']):
        return 7  # 孔雀青
    # 日常
    else:
        return 10  # 罗勒绿

def cal_list(start=None, end=None, max_results=20):
    """List calendar events"""
    access_token = get_cal_token()
    session = get_session()
    headers = {'Authorization': f'Bearer {access_token}'}

    now = datetime.datetime.utcnow()
    if not start:
        start = (now - datetime.timedelta(hours=12)).isoformat() + 'Z'
    if not end:
        end = (now + datetime.timedelta(days=7)).isoformat() + 'Z'

    params = {
        'calendarId': 'primary',
        'timeMin': start,
        'timeMax': end,
        'maxResults': max_results,
        'singleEvents': True,
        'orderBy': 'startTime'
    }

    resp = session.get(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        headers=headers, params=params, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    data = resp.json()
    events = data.get('items', [])
    if not events:
        print("No events found.")
        return

    print(f"\nEvents ({len(events)}):")
    print("-" * 60)
    for e in events:
        event_id = e.get('id', '')
        start_val = e['start'].get('dateTime', e['start'].get('date', 'all-day'))
        end_val = e['end'].get('dateTime', e['end'].get('date', ''))
        summary = e.get('summary', '(no title)')
        status = e.get('status', '')
        loc = e.get('location', '')
        completed = ' [✓ DONE]' if status == 'confirmed' and e.get('transparency') == 'transparent' else ''
        color = e.get('colorId', '')
        color_str = f' [🎨 {color}]' if color else ''
        print(f"* {summary}{completed}{color_str}")
        print(f"  ID: {event_id}")
        print(f"  Start: {start_val}")
        if end_val:
            print(f"  End:   {end_val}")
        if loc:
            print(f"  Location: {loc}")
        print()

def cal_add(summary, start_time, end_time, description='', location='', color_id=None):
    """Add a calendar event"""
    access_token = get_cal_token()
    session = get_session()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    if 'T' not in start_time:
        start_time += 'T00:00:00+08:00'
    if 'T' not in end_time:
        end_time += 'T23:59:59+08:00'

    event = {
        'summary': summary,
        'start': {'dateTime': start_time},
        'end': {'dateTime': end_time},
    }
    if description:
        event['description'] = description
    if location:
        event['location'] = location

    # 颜色设置
    if color_id:
        event['colorId'] = str(color_id)
    else:
        assigned_color = auto_assign_color(summary, description)
        event['colorId'] = str(assigned_color)

    resp = session.post(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        headers=headers, json=event, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    e = resp.json()
    color_used = e.get('colorId', 'auto')
    print(f"Event created: {e.get('htmlLink', e['id'])}")
    print(f"Color: {color_used} (auto-assigned)" if not color_id else f"Color: {color_id}")

def cal_delete(event_id):
    """Delete a calendar event"""
    access_token = get_cal_token()
    session = get_session()
    headers = {'Authorization': f'Bearer {access_token}'}

    resp = session.delete(
        f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}',
        headers=headers, timeout=30
    )
    if resp.status_code == 204:
        print(f"Event deleted: {event_id}")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

def cal_update(event_id, **kwargs):
    """Update a calendar event"""
    access_token = get_cal_token()
    session = get_session()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    resp = session.get(
        f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}',
        headers=headers, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error fetching event: {resp.status_code} - {resp.text}")
        return

    event = resp.json()

    if 'summary' in kwargs:
        event['summary'] = kwargs['summary']
    if 'description' in kwargs:
        event['description'] = kwargs['description']
    if 'location' in kwargs:
        event['location'] = kwargs['location']
    if 'start' in kwargs:
        start_time = kwargs['start']
        if 'T' not in start_time:
            start_time += 'T00:00:00+08:00'
        event['start'] = {'dateTime': start_time}
    if 'end' in kwargs:
        end_time = kwargs['end']
        if 'T' not in end_time:
            end_time += 'T23:59:59+08:00'
        event['end'] = {'dateTime': end_time}
    if 'done' in kwargs:
        if kwargs['done']:
            event['transparency'] = 'transparent'
            event['status'] = 'confirmed'
        else:
            event.pop('transparency', None)
    if 'color' in kwargs:
        event['colorId'] = str(kwargs['color'])

    resp = session.put(
        f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}',
        headers=headers, json=event, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error updating event: {resp.status_code} - {resp.text}")
        return

    e = resp.json()
    print(f"Event updated: {e.get('htmlLink', event_id)}")

def cal_search(query, max_results=20):
    """Search calendar events"""
    access_token = get_cal_token()
    session = get_session()
    headers = {'Authorization': f'Bearer {access_token}'}

    now = datetime.datetime.utcnow()
    start = (now - datetime.timedelta(days=30)).isoformat() + 'Z'
    end = (now + datetime.timedelta(days=365)).isoformat() + 'Z'

    params = {
        'calendarId': 'primary',
        'timeMin': start,
        'timeMax': end,
        'maxResults': max_results,
        'q': query,
        'singleEvents': True,
        'orderBy': 'startTime'
    }

    resp = session.get(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        headers=headers, params=params, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    data = resp.json()
    events = data.get('items', [])
    if not events:
        print(f"No events found matching '{query}'.")
        return

    print(f"\nSearch results for '{query}' ({len(events)}):")
    print("-" * 60)
    for e in events:
        event_id = e.get('id', '')
        start_val = e['start'].get('dateTime', e['start'].get('date', 'all-day'))
        summary = e.get('summary', '(no title)')
        print(f"* {summary}")
        print(f"  ID: {event_id}")
        print(f"  Start: {start_val}")
        print()

def cal_list_all():
    """List all calendars"""
    access_token = get_cal_token()
    session = get_session()
    headers = {'Authorization': f'Bearer {access_token}'}

    resp = session.get(
        'https://www.googleapis.com/calendar/v3/users/me/calendarList',
        headers=headers, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    data = resp.json()
    calendars = data.get('items', [])
    if not calendars:
        print("No calendars found.")
        return

    print(f"\nCalendars ({len(calendars)}):")
    print("-" * 60)
    for c in calendars:
        cal_id = c.get('id', '')
        summary = c.get('summary', '(no name)')
        primary = ' [PRIMARY]' if c.get('primary') else ''
        print(f"* {summary}{primary}")
        print(f"  ID: {cal_id}")
        print()

# ====== Task Functions ======
def task_list():
    """List all tasks"""
    access_token = get_task_token()
    session = get_session()
    headers = {'Authorization': f'Bearer {access_token}'}

    resp = session.get(
        'https://www.googleapis.com/tasks/v1/lists/@default/tasks',
        headers=headers,
        params={'showCompleted': 'true', 'showDeleted': 'false'},
        timeout=30
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    data = resp.json()
    tasks = data.get('items', [])

    if not tasks:
        print("No tasks found.")
        return

    active = [t for t in tasks if t.get('status') != 'completed']
    completed = [t for t in tasks if t.get('status') == 'completed']

    print(f"\nTasks ({len(active)} active, {len(completed)} completed):")
    print("-" * 60)

    if active:
        print("📋 Active:")
        for t in active:
            task_id = t.get('id', '')
            title = t.get('title', '(no title)')
            due = t.get('due', '')
            if due:
                due = due[:10]
            print(f"  ☐ {title}")
            print(f"    ID: {task_id}")
            if due:
                print(f"    Due: {due}")
            print()

    if completed:
        print("✅ Completed:")
        for t in completed:
            task_id = t.get('id', '')
            title = t.get('title', '(no title)')
            print(f"  ☑ {title}")
            print(f"    ID: {task_id}")
            print()

def task_add(title, notes='', due=''):
    """Add a new task"""
    access_token = get_task_token()
    session = get_session()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    task = {'title': title}
    if notes:
        task['notes'] = notes
    if due:
        if 'T' not in due:
            due += 'T00:00:00.000Z'
        task['due'] = due

    resp = session.post(
        'https://www.googleapis.com/tasks/v1/lists/@default/tasks',
        headers=headers, json=task, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    t = resp.json()
    print(f"Task created: {t.get('id')}")
    if t.get('selfLink'):
        print(f"Link: {t['selfLink']}")

def task_done(task_id):
    """Mark a task as completed"""
    access_token = get_task_token()
    session = get_session()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    resp = session.get(
        f'https://www.googleapis.com/tasks/v1/lists/@default/tasks/{task_id}',
        headers=headers, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error fetching task: {resp.status_code} - {resp.text}")
        return

    task = resp.json()
    task['status'] = 'completed'

    resp = session.put(
        f'https://www.googleapis.com/tasks/v1/lists/@default/tasks/{task_id}',
        headers=headers, json=task, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error updating task: {resp.status_code} - {resp.text}")
        return

    print(f"Task marked as done: {task_id}")

def task_delete(task_id):
    """Delete a task"""
    access_token = get_task_token()
    session = get_session()
    headers = {'Authorization': f'Bearer {access_token}'}

    resp = session.delete(
        f'https://www.googleapis.com/tasks/v1/lists/@default/tasks/{task_id}',
        headers=headers, timeout=30
    )
    if resp.status_code == 204:
        print(f"Task deleted: {task_id}")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

def task_update(task_id, **kwargs):
    """Update a task"""
    access_token = get_task_token()
    session = get_session()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    resp = session.get(
        f'https://www.googleapis.com/tasks/v1/lists/@default/tasks/{task_id}',
        headers=headers, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error fetching task: {resp.status_code} - {resp.text}")
        return

    task = resp.json()

    if 'title' in kwargs:
        task['title'] = kwargs['title']
    if 'notes' in kwargs:
        task['notes'] = kwargs['notes']
    if 'due' in kwargs:
        due = kwargs['due']
        if 'T' not in due:
            due += 'T00:00:00.000Z'
        task['due'] = due

    resp = session.put(
        f'https://www.googleapis.com/tasks/v1/lists/@default/tasks/{task_id}',
        headers=headers, json=task, timeout=30
    )
    if resp.status_code != 200:
        print(f"Error updating task: {resp.status_code} - {resp.text}")
        return

    print(f"Task updated: {task_id}")

# ====== Main ======
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    # Auth
    if cmd == 'auth':
        auth()

    # Calendar commands
    elif cmd == 'list':
        start = sys.argv[2] if len(sys.argv) > 2 else None
        end = sys.argv[3] if len(sys.argv) > 3 else None
        cal_list(start, end)

    elif cmd == 'add':
        if len(sys.argv) < 4:
            print("Usage: python google-planner.py add <title> <start> <end> [description] [location] [--color <1-11>]")
            print("Date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
            sys.exit(1)
        summary = sys.argv[2]
        start = sys.argv[3]
        end = sys.argv[4]
        desc = ''
        loc = ''
        color_id = None
        i = 5
        while i < len(sys.argv):
            if sys.argv[i] == '--color' and i + 1 < len(sys.argv):
                color_id = int(sys.argv[i + 1])
                i += 2
            else:
                if not desc:
                    desc = sys.argv[i]
                elif not loc:
                    loc = sys.argv[i]
                i += 1
        cal_add(summary, start, end, desc, loc, color_id)

    elif cmd == 'delete':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py delete <event_id>")
            sys.exit(1)
        cal_delete(sys.argv[2])

    elif cmd == 'update':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py update <event_id> [options]")
            print("Options: --summary <title> --desc <description> --loc <location>")
            print("         --start <date> --end <date> --done --color <1-11>")
            sys.exit(1)
        event_id = sys.argv[2]
        kwargs = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--summary' and i + 1 < len(sys.argv):
                kwargs['summary'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--desc' and i + 1 < len(sys.argv):
                kwargs['description'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--loc' and i + 1 < len(sys.argv):
                kwargs['location'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--start' and i + 1 < len(sys.argv):
                kwargs['start'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--end' and i + 1 < len(sys.argv):
                kwargs['end'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--done':
                kwargs['done'] = True; i += 1
            elif sys.argv[i] == '--color' and i + 1 < len(sys.argv):
                kwargs['color'] = int(sys.argv[i + 1]); i += 2
            else:
                i += 1
        cal_update(event_id, **kwargs)

    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py search <keyword>")
            sys.exit(1)
        cal_search(sys.argv[2])

    elif cmd == 'calendars':
        cal_list_all()

    # Task commands
    elif cmd == 'tasks':
        task_list()

    elif cmd == 'task-add':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py task-add <title> [notes] [due]")
            print("Due format: YYYY-MM-DD")
            sys.exit(1)
        title = sys.argv[2]
        notes = sys.argv[3] if len(sys.argv) > 3 else ''
        due = sys.argv[4] if len(sys.argv) > 4 else ''
        task_add(title, notes, due)

    elif cmd == 'task-done':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py task-done <task_id>")
            sys.exit(1)
        task_done(sys.argv[2])

    elif cmd == 'task-delete':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py task-delete <task_id>")
            sys.exit(1)
        task_delete(sys.argv[2])

    elif cmd == 'task-update':
        if len(sys.argv) < 3:
            print("Usage: python google-planner.py task-update <task_id> [options]")
            print("Options: --title <title> --notes <notes> --due <date>")
            sys.exit(1)
        task_id = sys.argv[2]
        kwargs = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
                kwargs['title'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--notes' and i + 1 < len(sys.argv):
                kwargs['notes'] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == '--due' and i + 1 < len(sys.argv):
                kwargs['due'] = sys.argv[i + 1]; i += 2
            else:
                i += 1
        task_update(task_id, **kwargs)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
