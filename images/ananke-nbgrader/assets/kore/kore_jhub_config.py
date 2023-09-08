# configure nbgrader and Kore

import logging
import os
import asyncio
import re
import subprocess
import json
import fcntl
import secrets
import sys
import pwd
from nbgrader.api import Gradebook  # noqa
from traitlets.config import Config

sys.path.append('/opt/kore')
from kore_utils import *

c = get_config()  # noqa

# Remove hidden tests from feedback? (default value for new courses)
remove_hidden = True

# Remove tracebacks of hidden tests from feedback? (default value for new courses)
remove_hidden_trace = True
 
# initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# API tokens
kore_token = secrets.token_hex(32)

# ensure existence of grader user accounts for all grader home directories
# (this is necessary after replacing the container with a new one)
for directory in os.listdir('/home'):
    if os.path.isdir(f'/home/{directory}'):
        try:
            pwd.getpwnam(directory)
        except KeyError:
            os.system(f'useradd --shell=/bin/bash {directory}')
            os.system(f'usermod -L {directory}')
            os.system(f'chown -R {directory}:{directory} /home/{directory}')
            
# instructors list (nbgrader extensions are already enabled if in list)
logging.info('Reading instructors data base')
instructors_path = '/opt/kore/runtime/instructors.json'
try:
    with open(instructors_path) as f:
        instructors = json.load(f)
except:
    logging.info('No instructors data base found, creating new one.')
    instructors = []
logging.debug('found {} instructors'.format(len(instructors)))

# post authentication callback for nbgrader configuration
async def nbgrader_post_auth(authenticator, handler, authentication):
    
    def get_dir_owner(path):
        ''' Return uid and gid of directory. '''
        if os.path.isdir(path):
            info = os.stat(path)
            return info.st_uid, info.st_gid
        else:
            return None, None
    
    def set_dir_owner(path, uid, gid):
        ''' Set directory's owner recursively if uid and gid both are not None. '''
        if uid and gid:
            os.system(f'chown -R {uid}:{gid} {path}')

    async def run_as_user(username, cmd, args):
        ''' Run command as dynamic user in username's home directory.
            cmd is a string. args is a list of strings. '''
        systemd_run = ['systemd-run',
                       '--wait',
                       f'--unit=post-auth-hook-{username}',
                       f'--working-directory=/var/lib/{username}',
                       '--property=DynamicUser=yes',
                       f'--property=StateDirectory={username}',
                       f'--property=Environment=HOME=/var/lib/{username}',
                       cmd] + args
        proc = await asyncio.create_subprocess_exec(*systemd_run)
        await proc.wait()
        
    logging.debug('Running nbgrader post authentication hook')
    needs_restart = False
    
    username = authentication.get('name')
    auth_state = authentication.get('auth_state')
    if 'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor' in auth_state.get('https://purl.imsglobal.org/spec/lti/claim/roles', []):
        is_instructor = True
    else:
        is_instructor = False
    user_home = f'/var/lib/private/{username}'

    # instructor user and first visit ==> acitvate extensions and add to db
    if is_instructor and username not in instructors:
        
        # activate nbgrader extensions for instructor
        logging.debug('activating nbgrader extensions for instructor')
        if is_instructor:
            uid, gid = get_dir_owner(user_home)
            await run_as_user(username, 'jupyter', ['server', 'extension', 'enable', '--user', 'nbgrader.server_extensions.course_list'])
            await run_as_user(username, 'jupyter', ['labextension', 'disable', '--level=user', 'nbgrader:course-list'])
            await run_as_user(username, 'jupyter', ['labextension', 'enable', '--level=user', 'nbgrader:course-list'])
            set_dir_owner(user_home, uid, gid)

        # add instructor to list
        instructors.append(username)
        with open(instructors_path, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(instructors, f)
            fcntl.flock(f, fcntl.LOCK_UN)
            os.system(f'chmod 600 {instructors_path}')

    # write instructor's LTI data to file (read by Kore)
    if is_instructor:
        lti_json_path = f'/opt/kore/runtime/lti_{username}.json'
        with open(lti_json_path, 'w') as f:
            json.dump(auth_state, f)
        os.system(f'chmod 600 {lti_json_path}')

    # make course title and id
    course_id, course_title, grader_user = make_course_id(auth_state)
    logging.debug(f'course title: {course_title}')
    logging.debug(f'course id: {course_id}')
    logging.debug(f'grader user: {grader_user}')

    # check existence of grader user
    grader_exists = os.path.isdir(f'/home/{grader_user}')

    # create grader user if necessary
    if is_instructor and not grader_exists:
        logging.info(f'Creating grader user {grader_user}')
        
        # user account
        os.system(f'useradd --create-home --shell=/bin/bash {grader_user}')
        os.system(f'usermod -L {grader_user}')

        # nbgrader extensions
        os.system(f'runuser -u {grader_user} -- jupyter server extension enable --user nbgrader.server_extensions.formgrader')
        os.system(f'runuser -u {grader_user} -- jupyter server extension disable --user nbgrader.server_extensions.assignment_list')
        os.system(f'runuser -u {grader_user} -- jupyter server extension disable --user nbgrader.server_extensions.validate_assignment')
        os.system(f'runuser -u {grader_user} -- jupyter labextension disable --level=user nbgrader:formgrader')
        os.system(f'runuser -u {grader_user} -- jupyter labextension enable --level=user nbgrader:formgrader')
        os.system(f'runuser -u {grader_user} -- jupyter labextension disable --level=user nbgrader:assignment-list')
        os.system(f'runuser -u {grader_user} -- jupyter labextension disable --level=user nbgrader:create-assignment')
        os.system(f'runuser -u {grader_user} -- jupyter labextension enable --level=user nbgrader:create-assignment')
        os.system(f'runuser -u {grader_user} -- jupyter labextension disable --level=user nbgrader:validate-assignment')

        # create nbgrader config and course directory
        config_content = '\n'.join([
            'c = get_config()',
            '',
            f'c.CourseDirectory.root = \'/home/{grader_user}/course_data\'',
            f'c.CourseDirectory.course_id = \'{course_id}\'',
            '',
            'c.GenerateFeedback.preprocessors = [',
            '    \'nbgrader.preprocessors.GetGrades\',',
            '    \'nbconvert.preprocessors.CSSHTMLHeaderPreprocessor\',',
            '    # uncomment next line to remove hidden tests from feedback',
            '    ' + ('' if remove_hidden else '#') + '\'nbgrader.preprocessors.ClearHiddenTests\',',
            '    # uncomment next line to remove tracebacks of hidden tests from feedback',
            '    ' + ('' if remove_hidden_trace else '#') + '\'nbgrader.preprocessors.Execute\',',
            ']'
        ])
        with open(f'/home/{grader_user}/.jupyter/nbgrader_config.py', 'w') as f:
            f.write(config_content)
        os.system(f'mkdir /home/{grader_user}/course_data')
        with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
            pass # do nothing, just create gradebook.db here and set permissions (next line)
        os.system(f'chown -R {grader_user}:{grader_user} /home/{grader_user}')
        os.system(f'chmod -R go-rwx /home/{grader_user}')

    # create grader service if necessary
    if is_instructor:
            
        # read services, roles, groups from config file
        services, roles, groups = read_autogenerated_config()
        
        # create formgrader service
        for service in services: # service already there?
            if service['name'] == course_id:
                logging.debug('course exists')
                break
        else: # it's a new course
            logging.info(f'creating new nbgrader course {course_id}')
            if len(services) == 0:
                port = 8100
            else:
                port = max([int(service['url'].split(':')[-1]) for service in services]) + 1
            services.append({
                'name': course_id,
                'url': f'http://127.0.0.1:{port}',
                'command': ['jupyterhub-singleuser', f'--group=formgrade-{course_id}'],# '--debug'],
                'user': grader_user,
                'cwd': f'/home/{grader_user}',
                'api_token': secrets.token_hex(32),
                'oauth_no_confirm': True
            })
            for role in roles:
                if role.get('name') == 'formgrader-service-role':  # formgrader role exists
                    role['services'].append(course_id)
                    break
            else:  # no formgrader role (we are creating the first formgrader service)
                roles.append({
                    'name': 'formgrader-service-role',
                    'scopes': ['read:users:groups', 'list:services', 'list:users', 'groups', 'admin:users', 'admin:groups'],
                    'services': [course_id]
                })
            roles.append({
                'name': f'formgrader-{course_id}-role',
                'groups': [f'formgrade-{course_id}'],
                'scopes': [f'access:services!service={course_id}',
                           f'list:services!service={course_id}',
                           f'read:services!service={course_id}',
                           'access:services!service=kore']
            })
            groups.update({
                f'formgrade-{course_id}': [grader_user],
                f'nbgrader-{course_id}': [grader_user]
            })
            needs_restart = True

        # add instructor to course
        group_name = f'formgrade-{course_id}'
        if username not in groups[group_name]:
            groups[group_name].append(username)
            needs_restart = True
            
        # write services, roles, groups to config file
        write_autogenerated_config(services, roles, groups)
    
    # write course title to global nbgrader_config.py
    if is_instructor:
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
        mapping[course_id] = course_title
        with open('/opt/conda/envs/jhub/etc/jupyter/nbgrader_config.py', 'w') as f:
            f.write(pre)
            f.write(f'c.NbGrader.course_titles = {str(mapping)}')
            f.write(post)
    
    # add student to course
    if grader_exists and not is_instructor:

        # add student to nbgrader data base
        with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
            gb.update_or_create_student(
                username,
                first_name=auth_state.get('given_name', 'none'),
                last_name=auth_state.get('family_name', 'none'),
                email=auth_state.get('email', 'none'),
                lms_user_id=auth_state['sub']
            )
        
        # add student to course's JupyterHub group (required by nbgrader)
        base_url = get_hub_base_url(auth_state)
        logging.debug('adding student to course\'s nbgrader group')
        subprocess.run(['systemd-run', '--on-active=5', 'curl',
                        '-H', 'Content-Type: application/json',
                        '-H', 'Accept: application/json',
                        '-H', f'Authorization: token {kore_token}',
                        '-X', 'POST',
                        '-d', '{"users":["' + username + '"]}',
                        f'http://127.0.0.1:8081/{base_url}hub/api/groups/nbgrader-{course_id}/users'])

    return needs_restart

c.post_auth_hook_callbacks.append(nbgrader_post_auth)

# grant permissions of user to its single-user server (else course list extension cannot read service list)
c.JupyterHub.load_roles.append({
    'name': 'server',
    'scopes': ['inherit'],
})

# Kore service
c.JupyterHub.services.append({
    'name': 'kore',
    'url': 'http://127.0.0.1:10001',
    'api_token': kore_token,
    'oauth_no_confirm': True,
    'cwd': '/opt/kore',
    'command': ['gunicorn', '--workers=2', '--bind=localhost:10001', 'kore:app']
})
c.JupyterHub.load_roles.append({
    'name': 'kore_role',
    'scopes': ['groups', 'read:users'],
    'services': ['kore']
})
 
# autogenerated services
load_subconfig('/opt/kore/runtime/autogenerated_services.py')
