import datetime
import json
from jwcrypto.jwk import JWK
import logging
import os
import re
import secrets
import subprocess
import time
from functools import wraps
from tempfile import mkdtemp

import jwt
import requests
from flask import Flask
from flask import jsonify as flask_jsonify
from flask import make_response
from flask import redirect as flask_redirect
from flask import render_template
from flask import request as flask_request
from flask import session as flask_session
from flask_session import Session
from jupyterhub.services.auth import HubOAuth
from nbgrader.api import Gradebook
from traitlets.config import Config

from kore_utils import *

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=secrets.token_bytes(32),
    SESSION_COOKIE_NAME='kore-sessionid',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,   # should be True in case of HTTPS usage (production)
    SESSION_COOKIE_SAMESITE=None,  # should be 'None' in case of HTTPS usage (production)
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=mkdtemp(),
    DEBUG_TB_INTERCEPT_REDIRECTS=False
)
Session(app)    # store session data on server (not on client)

# read LTI configuration from ltiauthenticator's config
with open('/opt/conda/envs/jhub/etc/jupyterhub/jupyterhub_config.d/30_lms.py') as f:
    config_code = f.read()
config_code = config_code.replace('c = get_config()', '')
config_code = config_code.replace('c.LTI13Authenticator.', '')
exec(config_code)
lti_config = {
    'client_id': client_id,
    'issuer': issuer,
    'authorize_url': authorize_url,
    'jwks_endpoint': jwks_endpoint,
    'access_token_url': access_token_url
}
logging.info('LTI config for Kore: ' + str(lti_config))


prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')
logging.info(f'JupyterHub service prefix for Kore: {prefix}')

kore_token = os.environ['JUPYTERHUB_API_TOKEN']
auth = HubOAuth(api_token=kore_token, cache_max_age=60)

def authenticated(f):
    """
    Decorator function for authenticating with the Hub via OAuth.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = flask_session.get('token')
        if token:
            user = auth.user_for_token(token)
        else:
            user = None
        if user:
            return f(user, *args, **kwargs)
        else:
            # redirect to login url on failed auth
            state = auth.generate_state(next_url=flask_request.path)
            response = make_response(flask_redirect(auth.login_url + f'&state={state}'))
            response.set_cookie(auth.state_cookie_name, state)
            return response
    return decorated

@app.route(prefix + 'oauth_callback')
def oauth_callback():
    code = flask_request.args.get('code', None)
    if code is None:
        return 403

    # validate state field
    arg_state = flask_request.args.get('state', None)
    cookie_state = flask_request.cookies.get(auth.state_cookie_name)
    if arg_state is None or arg_state != cookie_state:
        # state doesn't match
        return 403

    token = auth.token_for_code(code)
    flask_session['token'] = token
    next_url = auth.get_next_url(cookie_state) or prefix
    response = make_response(flask_redirect(next_url))
    return response


@app.route(prefix + '/jwks', methods=['GET'])
def get_jwks():
    
    # read JWK from file
    with open('keys/lti_key.json') as f:
        jwk = json.load(f)
        
    # make JWKS containing the read JWK only
    jwks = {'keys': [jwk]}
    
    return flask_jsonify(jwks)


@app.route(prefix)
@authenticated
def home(user):
    
    tmpl_data = {}    # data relevant to HTML template
    tmpl_data['prefix'] = prefix

    username = user.get('name')
    logging.debug(f'User: {username}')
    tmpl_data['username'] = username

    # get and show LTI data
    try:
        with open(f'runtime/lti_{username}.json') as f:
            lti_state = json.load(f)
    except:
        logging.error(f'LTI state for user {username} not available!')
        tmpl_data['message'] = 'LTI state not found! Try to login again.'
        return render_template('error.html.jinja', data=tmpl_data)
    tmpl_data['lti_state'] = lti_state

    # show LTI user info
    tmpl_data['first_name'] = lti_state.get('given_name')
    tmpl_data['last_name'] = lti_state.get('family_name')

    # get and show current course's info
    login_course_id, login_course_title, login_grader_user = make_course_id(lti_state)
    tmpl_data['login_course_title'] = login_course_title
    tmpl_data['login_course_id'] = login_course_id
    logging.debug(f'Course: {login_course_id}')
    
    # get admin state
    base_url = get_hub_base_url(lti_state)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'token {kore_token}',
    }
    response = requests.get(f'http://127.0.0.1:8081/{base_url}hub/api/users/{username}', headers=headers)
    user_data = response.json()
    admin = user_data['admin']
    logging.debug(f'admin: {admin}')
    
    # get user's courses and corresponding instructors
    services, roles, groups = read_autogenerated_config()
    course_ids = []
    instructors = {}
    for group in groups:
        if group.startswith('formgrade-'):
            if username in groups[group] or admin:
                course_id = group[len('formgrade-'):]
                course_ids.append(course_id)
                instructors[course_id] = []
                for user in groups[group]:
                    if not user.startswith('u'): # don't show grader user
                        continue
                    try:
                        with open(f'runtime/lti_{user}.json') as f:
                            user_lti_state = json.load(f)
                        full_name = str(user_lti_state.get('given_name')) + ' ' + str(user_lti_state.get('family_name'))
                        instructors[course_id].append(f'{full_name} ({user})')
                    except:  # no LTI state available for instructor
                        instructors[course_id].append(user)
                    
    tmpl_data['course_ids'] = course_ids
    tmpl_data['instructors'] = instructors
        
        
    return render_template('home.html.jinja', data=tmpl_data)


@app.route(prefix + '/send_all')
@authenticated
def send_all(user):

    tmpl_data = {}    # data relevant to HTML template
    tmpl_data['message'] = 'somthing went wrong, grades NOT sent'

    username = user.get('name')
    
    with open(f'runtime/lti_{username}.json') as f:
        lti_state = json.load(f)

    course_id, course_title, grader_user = make_course_id(lti_state)

    # create token for requesting access token from LMS
    auth_token_request_data = {
        'iss': lti_state['aud'],
        'aud': lti_config['issuer'],
        'sub': lti_state['aud'],
        'iat': int(time.time()) - 5,
        'exp': int(time.time()) + 60,
    }

    # sign token
    with open('keys/lti_key') as f:
        private_key = f.read()
    with open('keys/lti_key.json') as f:
        jwk = json.load(f)
    token = jwt.encode(auth_token_request_data, private_key, algorithm='RS256', headers={'kid': jwk['kid']})

    # get access token from LMS
    params = {
        'grant_type': 'client_credentials',
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': token,
        'scope': 'https://purl.imsglobal.org/spec/lti-ags/scope/score https://purl.imsglobal.org/spec/lti-ags/scope/lineitem'
    }
    response = requests.post(lti_config['access_token_url'], data=params)
    access_token = response.json()['access_token']
        
    # get score URL from line items
    url, args = lti_state['https://purl.imsglobal.org/spec/lti-ags/claim/endpoint']['lineitem'].split('?')
    score_url = url + '/scores?' + args

    # get users and scores from gradebook
    student_ids = []
    scores = []
    max_scores = []
    tmpl_data['students'] = []
    with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
        for student in gb.students:
            student_ids.append(student.lms_user_id)
            scores.append(student.score)
            max_scores.append(student.max_score)
            tmpl_data['students'].append({
                'first_name': student.first_name,
                'last_name': student.last_name,
                'id': student.id,
                'score': student.score,
                'max_score': student.max_score
            })

    # prepare (user independent) score data for sending
    params = {
        'activityProgress': 'Completed',
        'gradingProgress': 'FullyGraded',
        'timestamp': datetime.datetime.now().astimezone().isoformat(),
        'userId': '',
        'comment': '',
    }
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/vnd.ims.lis.v1.score+json'
    }
    
    # send scores
    for student_id, score, max_score in zip(student_ids, scores, max_scores):
        params['userId'] = student_id
        params['scoreGiven'] = score
        params['scoreMaximum'] = max_score
        response = requests.post(score_url, json=params, headers=headers)

    if response.status_code == 200:
        tmpl_data['message'] = 'grades sent successfully'

    tmpl_data['prefix'] = prefix
    tmpl_data['username'] = username
    tmpl_data['course_title'] = course_title
    tmpl_data['course_id'] = course_id
    tmpl_data['lti_state'] = lti_state
    
    return render_template('sending_grades.html.jinja', data=tmpl_data)


@app.route(prefix + '/remove_course', methods=['GET'])
@authenticated
def remove(user):

    tmpl_data = {}    # data relevant to HTML template
    tmpl_data['prefix'] = prefix

    username = user.get('name')
    logging.debug(f'User: {username}')
    tmpl_data['username'] = username

    with open(f'runtime/lti_{username}.json') as f:
        lti_state = json.load(f)

    course_id = flask_request.args.get('course_id')
    ask = True if flask_request.args.get('ask') != 'no' else False
    tmpl_data['course_id'] = course_id
    
    if ask:
        return render_template('remove_ask.html.jinja', data=tmpl_data)

    # get admin state
    base_url = get_hub_base_url(lti_state)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'token {kore_token}',
    }
    response = requests.get(f'http://127.0.0.1:8081/{base_url}hub/api/users/{username}', headers=headers)
    user_data = response.json()
    admin = user_data['admin']
    logging.debug(f'admin: {admin}')

    services, roles, groups = read_autogenerated_config()

    group = groups.get(f'formgrade-{course_id}')
    if not group:
        tmpl_data['message'] = f'Course {course_id} not found!'
        return render_template('remove_error.html.jinja', data=tmpl_data)
    if not admin and username not in group:
        tmpl_data['message'] = f'Something went wrong! You are not an instructor of course {course_id}. Not removing course.'
        return render_template('remove_error.html.jinja', data=tmpl_data)
    del groups[f'formgrade-{course_id}']
    logging.debug(f'Removed group for course {course_id}')
        
    for role in roles:
        if role.get('name') == f'formgrader-{course_id}-role':
            del roles[roles.index(role)]
            logging.debug(f'Removed role for course {course_id}')
        if role.get('name') == 'formgrader-service-role':
            del role['services'][role['services'].index(course_id)]

    for service in services:
        if service['name'] == course_id:
            del services[services.index(service)]
            logging.debug(f'Removed service {course_id}')
            break

    write_autogenerated_config(services, roles, groups)

    os.system(f'rm -r /opt/nbgrader_exchange/{course_id}')
    logging.debug(f'Removed nbgrader exchange for course {course_id}')
    
    grader_user = course_id_to_grader_user(course_id)
    os.system(f'userdel {grader_user}')
    os.system(f'rm -r /home/{grader_user}')
    logging.debug(f'Removed grader user for course {course_id}')
    
    with open('/opt/conda/envs/jhub/etc/jupyter/nbgrader_config.py') as f:
        content = f.read()
    start = content.find('c.NbGrader.course_titles')
    end = content.find('}', start)
    pre = content[:start]
    code = content[start:end+1]
    post = content[end+1:]
    code = code.replace('c.NbGrader.course_titles = ', 'mapping.update(')
    code = code.replace('}', '})')
    mapping = {}
    exec(code + '\n')
    if course_id in mapping.keys():
        del mapping[course_id]
    with open('/opt/conda/envs/jhub/etc/jupyter/nbgrader_config.py', 'w') as f:
        f.write(pre)
        f.write(f'c.NbGrader.course_titles = {str(mapping)}')
        f.write(post)
    
    
    logging.info('restarting hub in 3 seconds...')
    subprocess.run(['systemd-run', '--on-active=3', 'systemctl', 'restart', 'jupyterhub'])
    
    return render_template('remove_success.html.jinja', data=tmpl_data)


@app.route(prefix + '/reset_course', methods=['GET'])
@authenticated
def reset(user):

    tmpl_data = {}    # data relevant to HTML template
    tmpl_data['prefix'] = prefix

    username = user.get('name')
    logging.debug(f'User: {username}')
    tmpl_data['username'] = username

    with open(f'runtime/lti_{username}.json') as f:
        lti_state = json.load(f)

    course_id = flask_request.args.get('course_id')
    ask = True if flask_request.args.get('ask') != 'no' else False
    tmpl_data['course_id'] = course_id
    
    if ask:
        return render_template('reset_ask.html.jinja', data=tmpl_data)

    # get admin state
    base_url = get_hub_base_url(lti_state)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'token {kore_token}',
    }
    response = requests.get(f'http://127.0.0.1:8081/{base_url}hub/api/users/{username}', headers=headers)
    user_data = response.json()
    admin = user_data['admin']
    logging.debug(f'admin: {admin}')

    services, roles, groups = read_autogenerated_config()

    group = groups.get(f'formgrade-{course_id}')
    if not group:
        tmpl_data['message'] = f'Course {course_id} not found!'
        return render_template('reset_error.html.jinja', data=tmpl_data)
    if not admin and username not in group:
        tmpl_data['message'] = f'Something went wrong! You are not an instructor of course {course_id}. Not resetting course.'
        return render_template('reset_error.html.jinja', data=tmpl_data)

    # remove students from gradebook (including submissions)
    grader_user = course_id_to_grader_user(course_id)
    with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
        usernames = [student.id for student in gb.students]
        for username in usernames:
            gb.remove_student(username)

    # remove students from course's nbgrader group
    base_url = get_hub_base_url(lti_state)
    logging.debug(f'removing all students from nbgrader group of course {course_id}')
    subprocess.run(['systemd-run', 'curl',
                    '-H', 'Content-Type: application/json',
                    '-H', 'Accept: application/json',
                    '-H', f'Authorization: token {kore_token}',
                    '-X', 'DELETE',
                    '-d', '{"users":' + json.dumps(usernames) + '}',
                    f'http://127.0.0.1:8081/{base_url}hub/api/groups/nbgrader-{course_id}/users'])
    
    # clean up nbgrader exchange
    os.system(f'rm -r /opt/nbgrader_exchange/{course_id}')
    
    # clean up course directory
    os.system(f'rm /home/{grader_user}/course_data/gradebook.db')
    os.system(f'rm -r /home/{grader_user}/course_data/autograded')
    os.system(f'rm -r /home/{grader_user}/course_data/feedback')
    os.system(f'rm -r /home/{grader_user}/course_data/release')
    os.system(f'rm -r /home/{grader_user}/course_data/submitted')
    
    return render_template('reset_success.html.jinja', data=tmpl_data)


@app.route(prefix + '/backup_course', methods=['GET'])
@authenticated
def backup(user):

    tmpl_data = {}    # data relevant to HTML template
    tmpl_data['prefix'] = prefix

    username = user.get('name')
    logging.debug(f'User: {username}')
    tmpl_data['username'] = username

    with open(f'runtime/lti_{username}.json') as f:
        lti_state = json.load(f)

    course_id = flask_request.args.get('course_id')
    tmpl_data['course_id'] = course_id
    
    # get admin state
    base_url = get_hub_base_url(lti_state)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'token {kore_token}',
    }
    response = requests.get(f'http://127.0.0.1:8081/{base_url}hub/api/users/{username}', headers=headers)
    user_data = response.json()
    admin = user_data['admin']
    logging.debug(f'admin: {admin}')

    services, roles, groups = read_autogenerated_config()

    group = groups.get(f'formgrade-{course_id}')
    if not group:
        tmpl_data['message'] = f'Course {course_id} not found!'
        return render_template('backup_error.html.jinja', data=tmpl_data)
    if not admin and username not in group:
        tmpl_data['message'] = f'Something went wrong! You are not an instructor of course {course_id}. Backup not allowed.'
        return render_template('backup_error.html.jinja', data=tmpl_data)

    dest_path = f'/var/lib/private/{username}/backup_{course_id}'
    if os.path.exists(dest_path):
        tmpl_data['message'] = f'Destination path "backup_{course_id}" already exists. Backup FAILED!'
        return render_template('backup_error.html.jinja', data=tmpl_data)
    grader_user = course_id_to_grader_user(course_id)
    os.system(f'cp -r /home/{grader_user}/course_data {dest_path}')
    info = os.stat(f'/var/lib/private/{username}')
    os.system(f'chown -R {info.st_uid}:{info.st_gid} {dest_path}')
    
    return render_template('backup_success.html.jinja', data=tmpl_data)


@app.route(prefix + '/import_assignments', methods=['GET'])
@authenticated
def import_assignments(user):

    tmpl_data = {}    # data relevant to HTML template
    tmpl_data['prefix'] = prefix

    username = user.get('name')
    logging.debug(f'User: {username}')
    tmpl_data['username'] = username

    src_path = flask_request.args.get('path')
    if src_path.find('..') != -1:
        tmpl_data['message'] = f'Import path must not contain ".."!'
        return render_template('import_error.html.jinja', data=tmpl_data)    
    course_id = flask_request.args.get('course_id')
    tmpl_data['course_id'] = course_id
    
    services, roles, groups = read_autogenerated_config()

    group = groups.get(f'formgrade-{course_id}')
    if not group:
        tmpl_data['message'] = f'Course {course_id} not found!'
        return render_template('import_error.html.jinja', data=tmpl_data)
    if username not in group:
        tmpl_data['message'] = f'Something went wrong! You are not an instructor of course {course_id}. Importing assignments not allowed.'
        return render_template('backup_error.html.jinja', data=tmpl_data)

    src_path = f'/var/lib/private/{username}/{src_path}'
    grader_user = course_id_to_grader_user(course_id)
    dest_path = f'/home/{grader_user}/course_data/source'
    if os.path.exists(dest_path):
        files = os.listdir(dest_path)
        non_hidden = False
        for f in files:
            if f[0] != '.':
                non_hidden = True
                break
        if non_hidden:
            tmpl_data['message'] = f'There are assignments in {course_id}. Importing assignments not supported if course already has assignments.'
            return render_template('import_error.html.jinja', data=tmpl_data)
    os.system(f'rm -r {dest_path}')
    os.system(f'cp -r -P {src_path} {dest_path}')
    os.system(f'chown -R {grader_user}:{grader_user} {dest_path}')
    
    return render_template('import_success.html.jinja', data=tmpl_data)
