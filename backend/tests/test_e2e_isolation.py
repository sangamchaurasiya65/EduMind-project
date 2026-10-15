import urllib.request
import json
import io

BASE = 'http://127.0.0.1:8000/api'

def req(path, method='GET', data=None, token=None, content_type='application/json'):
    url = f'{BASE}{path}'
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if content_type:
        headers['Content-Type'] = content_type
    
    body = None
    if data:
        if isinstance(data, dict):
            body = json.dumps(data).encode('utf-8')
        elif isinstance(data, bytes):
            body = data

    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r) as resp:
        res_data = resp.read().decode('utf-8')
        return json.loads(res_data) if res_data else {}

import time

def test_full_user_lifecycle_and_multi_tenancy():
    ts = int(time.time())
    rohit_email = f'rohit_{ts}@edumind.ai'
    priya_email = f'priya_{ts}@edumind.ai'

    # 1. Register User 1: Rohit
    print(f'1. Registering Rohit ({rohit_email})...')
    req('/auth/register', 'POST', {
        'email': rohit_email,
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'full_name': 'Rohit Sharma'
    })
    rohit_auth = req('/auth/login', 'POST', {
        'email': rohit_email,
        'password': 'Password123!'
    })
    rohit_token = rohit_auth['access_token']
    print('Rohit logged in successfully.')

    # 2. Check Rohit fresh subjects and dashboard
    rohit_subs = req('/subjects/progress', token=rohit_token)
    assert len(rohit_subs) == 0, f'Expected 0 subjects for new user Rohit, got {len(rohit_subs)}'
    print('Rohit subjects list is correctly empty:', rohit_subs)

    rohit_dash = req('/dashboard/stats', token=rohit_token)
    assert rohit_dash['active_subjects_count'] == 0, 'Active subjects count not 0'
    assert len(rohit_dash['continue_learning']) == 0, 'Continue learning not empty'
    print('Rohit dashboard stats correctly 0.')

    # 3. Rohit uploads a material for new subject 'Operating Systems'
    boundary = '----WebKitFormBoundaryE2ETest123'
    parts = []
    def add_field(name, value):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode('utf-8'))

    add_field('title', 'OS Process Management Notes')
    add_field('subject_name', 'Operating Systems')
    add_field('subject_code', 'CS304')
    add_field('topic', 'Process Scheduling')
    add_field('difficulty_level', 'Intermediate')

    # file content > 100 chars
    file_bytes = b'Process management is an integral part of modern operating systems. The OS must allocate resources to processes, enable sharing of information, and synchronize execution.'
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="os_notes.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode('utf-8') + file_bytes + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
    multipart_body = b''.join(parts)

    upload_res = req('/materials/upload', 'POST', data=multipart_body, token=rohit_token, content_type=f'multipart/form-data; boundary={boundary}')
    print('Rohit material upload success:', upload_res.get('title'), 'status:', upload_res.get('status'))

    # 4. Check Rohit subjects again - now has Operating Systems
    rohit_subs_after = req('/subjects/progress', token=rohit_token)
    assert len(rohit_subs_after) == 1, f'Expected 1 subject for Rohit, got {len(rohit_subs_after)}'
    sub = rohit_subs_after[0]
    print(f'Subject created: name={sub["name"]}, code={sub["code"]}, progress={sub["progress_percent"]}%, status={sub["status"]}, materials_count={sub["materials_count"]}, current_topic={sub["current_topic"]}')
    assert sub['progress_percent'] == 0, 'New subject progress should be 0'
    assert sub['status'] == 'Not Started', 'New subject status should be Not Started'
    assert sub['materials_count'] == 1, 'Material count should be 1'
    assert sub['current_topic'] == 'Not started yet', 'Current topic should be Not started yet'

    # 5. Check Subject Detail and Chapters
    os_detail = req('/subjects/operating-systems/progress', token=rohit_token)
    print(f'OS Detail loaded: chapters={len(os_detail["chapters"])}, first chapter={os_detail["chapters"][0]["title"]}')
    assert len(os_detail['chapters']) >= 1, 'Expected at least 1 chapter from material'

    # 6. Register User 2: Priya
    print(f'2. Registering Priya ({priya_email})...')
    req('/auth/register', 'POST', {
        'email': priya_email,
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'full_name': 'Priya Patel'
    })
    priya_auth = req('/auth/login', 'POST', {
        'email': priya_email,
        'password': 'Password123!'
    })
    priya_token = priya_auth['access_token']
    print('Priya logged in successfully.')

    # 7. Check Priya subjects - MUST BE 0 (NO LEAK FROM ROHIT)
    priya_subs = req('/subjects/progress', token=priya_token)
    assert len(priya_subs) == 0, f'Expected 0 subjects for Priya, got {len(priya_subs)}'
    priya_dash = req('/dashboard/stats', token=priya_token)
    assert priya_dash['active_subjects_count'] == 0, 'Priya active subjects count not 0'
    assert len(priya_dash['continue_learning']) == 0, 'Priya continue learning not empty'
    print('Tenant isolation verified: Priya has 0 subjects and cannot see Rohit\'s Operating Systems.')

    print('\nALL E2E INTEGRATION CHECKS PASSED PERFECTLY!')

if __name__ == '__main__':
    test_full_user_lifecycle_and_multi_tenancy()
