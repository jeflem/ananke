# Configuration for nbgrader and Kore.

import asyncio
import fcntl
import json
import logging
import os
import pwd
import secrets
import subprocess
import sys
from subprocess import run, CalledProcessError

from ltiauthenticator.lti13.auth import LTI13Authenticator
from ltiauthenticator.lti13.handlers import LTI13CallbackHandler
from nbgrader.api import Gradebook

sys.path.append('/opt/kore')  # noqa
from exceptions import AutogeneratedFileError
from misc.utils import read_autogenerated_config, write_autogenerated_config, make_course_id, get_hub_base_url
from models.config_loaders import KoreConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

config_loader = KoreConfigLoader(kore_config_file_path='/opt/kore/config/config.json')
config_loader.load_config()

instructors_database_path = config_loader.instructors_database_path
nbgrader_config_path = config_loader.nbgrader_config_path
autogenerated_file_path = config_loader.autogenerated_file_path

c = get_config()  # noqa

# Remove hidden tests from feedback? (default value for new courses)
remove_hidden = True

# Remove tracebacks of hidden tests from feedback? (default value for new courses)
remove_hidden_trace = False

# API tokens
kore_token = secrets.token_hex(32)

# Ensure existence of grader user accounts for all grader home directories, which is necessary after replacing the container with a new one.
home_directory_root = '/home'
for directory in os.listdir(home_directory_root):
    directory_path = os.path.join(home_directory_root, directory)

    if os.path.isdir(directory_path):
        try:
            pwd.getpwnam(directory)
        except KeyError:
            try:
                run(['useradd', '--shell=/bin/bash', directory], check=True)
                run(['usermod', '-L', directory], check=True)
                run(['chown', '-R', f'{directory}:{directory}', directory_path], check=True)
            except CalledProcessError:
                logging.error('Command cannot be executed!')


# Read instructors list (nbgrader extensions are already enabled if in list)
logging.info('Reading instructors data base.')

instructors = []
try:
    with open(file=instructors_database_path, mode='r') as instructors_database:
        instructors = json.load(instructors_database)
except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError):
    logging.error('Error while accessing/parsing the instructor data base.')

logging.debug('found {} instructors'.format(len(instructors)))


# Post-authentication callback for nbgrader configuration.
async def nbgrader_post_auth(authenticator: LTI13Authenticator, handler: LTI13CallbackHandler, authentication: dict) -> bool:
    """
    This hook does a multiple of tasks, depending on the parameters from the authentication dict.
    (1) If the user is an instructor
    (1.1) ~ and it is the first login of the instructor to the `JupyterHub`, then
    (1.1.1) the nbgrader extensions get enabled for the instructor and
    (1.1.1) the user (instructor) is added to the corresponding database.
    (1.2) ~, then the LTI parameters are written to file.

    (2) The course parameters are generated, see the make_course_id function of the kore_utils.py file.

    (3) Check if a grader for the supplied course is present.
    (3.1) Where, if the user is an instructor and the grader does not yet exist, then
    (3.1.1) the grader user is created on the OS,
    (3.1.2) the nbgrader extensions are enabled,
    (3.1.3) the nbgrader config is generated and written to file and
    (3.1.4) the home directory creation and permission relevant task are handled.

    (4) If the user is an instructor and the course is not present as a service on the `JupyterHub`, then
    (4.1) the course gets added as a service,
    (4.2) the user (instructor) is added to the formgrade group of the service.

    (5) If the user is a student and the grader exists, then the user (student) gets added to the course.

    (6) Finally a bool is returned which indicates if the `JupyterHub` has to be restarted.

    Parameters
    ----------
    authenticator : LTI13Authenticator
        The JupyterHub LTI 1.3 Authenticator.
    handler : LTI13CallbackHandler
        Handles JupyterHub authentication requests responses according to the LTI 1.3 standard.
    authentication : dict
        The authentication dict for the user.

    Returns
    -------
    bool
        True if a restart of the JupyterHub is necessary, False otherwise.
    """

    def get_dir_owner(path) -> tuple[int, int] | tuple[None, None]:
        """
        Return uid and gid of given directory.

        Parameters
        ----------
        path : str
            Path to the directory.

        Returns
        -------
        tuple[int, int] | tuple[None, None]
            Depending on the fact if the supplied directory exists, the uid and the gid are returned as tuple of ints, a tuple of None otherwise.
        """

        if os.path.isdir(path):
            _info = os.stat(path)
            return _info.st_uid, _info.st_gid
        else:
            return None, None

    def set_dir_owner(path: str, uid: int, gid: int) -> None:
        """
        Set directory's owner recursively if uid and gid both are not None.

        Parameters
        ----------
        path : str
            Path to the directory.
        uid : int
            The user identifier (uid) of the directory.
        gid : int
            The group identifier (gid) of the directory.

        Returns
        -------
        None
        """

        if uid and gid:
            run(['chown', '-R', f'{uid}:{gid}', path], check=True)

    async def run_as_user(username: str, cmd: str, args: list[str]) -> None:
        """
        Run command as dynamic user in usernames home directory.
        cmd is a string. args is a list of strings.

        Parameters
        ----------
        username : str
            The user as which to execute a command.
        cmd : str
            The command to be executed.
        args : list[str]
            Additional arguments for the supplied command.

        Returns
        -------
        None
        """

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

    logging.debug('Running nbgrader post authentication hook.')
    needs_restart = False

    username = authentication.get('name')
    auth_state = authentication.get('auth_state')

    is_instructor = True if 'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor' in auth_state.get('https://purl.imsglobal.org/spec/lti/claim/roles', []) else False
    user_home = f'/var/lib/private/{username}'

    # If the user is an instructor and the first login on the server, then the extensions are activated and the user is added to the database.
    if is_instructor and username not in instructors:

        # Activate nbgrader and kore extensions for instructor user.
        logging.debug(f'Activating nbgrader extensions for user: {username}.')
        uid, gid = get_dir_owner(path=user_home)
        await run_as_user(username, 'jupyter', ['server', 'extension', 'enable', '--user', 'nbgrader.server_extensions.course_list'])
        os.system('jupyter labextension unlock @jupyter/nbgrader:course-list')
        await run_as_user(username, 'jupyter', ['labextension', 'disable', '--level=user', '@jupyter/nbgrader:course-list'])
        await run_as_user(username, 'jupyter', ['labextension', 'enable', '--level=user', '@jupyter/nbgrader:course-list'])
        os.system('jupyter labextension lock @jupyter/nbgrader:course-list')
        os.system('jupyter labextension unlock kore-extension')
        await run_as_user(username, 'jupyter', ['labextension', 'disable', '--level=user', 'kore-extension'])
        await run_as_user(username, 'jupyter', ['labextension', 'enable', '--level=user', 'kore-extension'])
        os.system('jupyter labextension lock kore-extension')
        set_dir_owner(path=user_home, uid=uid, gid=gid)

        # Add the user to the instructor list and write altered database to file.
        instructors.append(username)

        with open(file=instructors_database_path, mode='w') as instructors_database:
            fcntl.flock(instructors_database, fcntl.LOCK_EX)
            json.dump(instructors, instructors_database)
            fcntl.flock(instructors_database, fcntl.LOCK_UN)

            try:
                run(['chmod', '600', instructors_database_path], check=True)
            except CalledProcessError:
                logging.error('Command cannot be executed!')

    # Write the instructor's LTI data to file. These are read by Kore.
    if is_instructor:
        lti_file_path = f'/opt/kore/runtime/lti_{username}.json'
        try:
            with open(lti_file_path, mode='w') as lti_file:
                json.dump(auth_state, lti_file, ensure_ascii=False, indent=4)
            run(['chmod', '600', lti_file_path], check=True)
        except (FileNotFoundError, PermissionError, OSError):
            logging.error('LTI file cannot be opened/altered.')

    # Generate course title and id.
    course_id, course_title, course_title_short, grader_user = make_course_id(lti_state=auth_state)
    logging.debug(f'Course title: {course_title}.')
    logging.debug(f'Course id: {course_id}.')
    logging.debug(f'Grader user: {grader_user}.')

    # Check existence of grader user.
    grader_exists = os.path.isdir(f'/home/{grader_user}')

    # Create grader user if necessary.
    if is_instructor and not grader_exists:
        logging.info(f'Creating grader user: {grader_user}.')

        # Add non-existing user to system.
        try:
            run(['useradd', '--create-home', '--shell=/bin/bash', grader_user], check=True)
            run(['usermod', '-L', grader_user], check=True)
        except CalledProcessError:
            logging.error('Command cannot be executed!')

        # Activate nbgrader extensions for current user.
        try:
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'server', 'extension', 'enable', '--user', 'nbgrader.server_extensions.formgrader'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'server', 'extension', 'disable', '--user', 'nbgrader.server_extensions.assignment_list'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'server', 'extension', 'disable', '--user', 'nbgrader.server_extensions.validate_assignment'], check=True)

            os.system('jupyter labextension unlock @jupyter/nbgrader:formgrader')
            os.system('jupyter labextension unlock @jupyter/nbgrader:assignment-list')
            os.system('jupyter labextension unlock @jupyter/nbgrader:create-assignment')
            os.system('jupyter labextension unlock @jupyter/nbgrader:validate-assignment')
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'labextension', 'disable', '--level=user', '@jupyter/nbgrader:formgrader'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'labextension', 'enable', '--level=user', '@jupyter/nbgrader:formgrader'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'labextension', 'disable', '--level=user', '@jupyter/nbgrader:assignment-list'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'labextension', 'disable', '--level=user', '@jupyter/nbgrader:create-assignment'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'labextension', 'enable', '--level=user', '@jupyter/nbgrader:create-assignment'], check=True)
            run(['runuser', '-u', grader_user, '--', 'jupyter', 'labextension', 'disable', '--level=user', '@jupyter/nbgrader:validate-assignment'], check=True)
            os.system('jupyter labextension lock @jupyter/nbgrader:formgrader')
            os.system('jupyter labextension lock @jupyter/nbgrader:assignment-list')
            os.system('jupyter labextension lock @jupyter/nbgrader:create-assignment')
            os.system('jupyter labextension lock @jupyter/nbgrader:validate-assignment')
        except CalledProcessError:
            logging.error('Command cannot be executed!')

        # Create nbgrader config and course directory.
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

        try:
            run(['mkdir', f'/home/{grader_user}/course_data'], check=True)
        except CalledProcessError:
            logging.error('Command cannot be executed!')

        # Initialize SQLite database using Gradebook class from nbgrader.
        with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db'):
            pass

        # Change ownership and permissions.
        try:
            run(['chown', '-R', f'{grader_user}:{grader_user}', f'/home/{grader_user}'], check=True)
            run(['chmod', '-R', 'go-rwx', f'/home/{grader_user}'], check=True)
        except CalledProcessError:
            logging.error('Command cannot be executed!')

    # Write general data of course (e.g. title, id, ...) to a JSON file.
    info_file_path = f'/home/{grader_user}/course_data/info.json'
    if is_instructor and not os.path.exists(info_file_path):
        target_link_uri = auth_state['https://purl.imsglobal.org/spec/lti/claim/target_link_uri']
        target_link_uri = '/'.join(target_link_uri.strip('/').split('://')[-1].split('/')[1:]) + '/'
        target_link_uri = '' if target_link_uri == '/' else target_link_uri

        info = {
            'id': course_id,
            'title': course_title,
            'title_short': course_title_short,
            'grader_user': grader_user,
            'target_link_uri': target_link_uri,
            'aud': auth_state['aud'],
            'lineitem': auth_state['https://purl.imsglobal.org/spec/lti-ags/claim/endpoint']['lineitem']
        }

        try:
            with open(info_file_path, 'w', encoding='utf-8') as info_file:
                json.dump(info, info_file, ensure_ascii=False, indent=4)

            run(['chown', '-R', f'{grader_user}:{grader_user}', info_file_path], check=True)
            run(['chmod', '-R', 'go-rwx', info_file_path], check=True)
        except (FileNotFoundError, PermissionError, CalledProcessError, OSError):
            logging.error('Error while accessing info.json file.')

    # Create grader service if necessary.
    if is_instructor:

        # Read services, roles, groups from config file.
        services, roles, groups = read_autogenerated_config(autogenerated_file_path=config_loader.autogenerated_file_path)

        # Check if formgrader service is present otherwise create it.
        for service in services:
            if service['name'] == course_id:
                logging.debug('Course exists already.')
                break
        else:
            logging.info(f'Creating new nbgrader course: {course_id}.')

            # Defining port on which the service is running.
            port = 8100 if len(services) == 0 else max([int(service['url'].split(':')[-1]) for service in services]) + 1

            # Appending new service to existing ones.
            services.append({
                'name': course_id,
                'url': f'http://127.0.0.1:{port}',
                'command': ['jupyterhub-singleuser', f'--group=formgrade-{course_id}', '--KernelSpecManager.ensure_native_kernel=False'],  # '--debug'],
                'user': grader_user,
                'cwd': f'/home/{grader_user}',
                'api_token': secrets.token_hex(32),
                'oauth_no_confirm': True,
                'display': False
            })

            # Check if formgrader role exists otherwise create it.
            for role in roles:
                if role.get('name') == 'formgrader-service-role':
                    role['services'].append(course_id)
                    break
            else:
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

        # Add instructor to course.
        group_name = f'formgrade-{course_id}'
        if username not in groups[group_name]:
            groups[group_name].append(username)
            needs_restart = True

        # Write new services, roles, groups to config file.
        try:
            write_autogenerated_config(autogenerated_file_path=config_loader.autogenerated_file_path, services=services, roles=roles, groups=groups)
        except AutogeneratedFileError:
            logging.error('Configuration file could not be written. Please see logs and contact your administrator.')

    # Write course title to global nbgrader_config.py.
    if is_instructor:
        try:
            with open(file=nbgrader_config_path, mode='r') as nbgrader_config_file:
                content = nbgrader_config_file.read()
        except (FileNotFoundError, PermissionError, OSError):
            logging.error('Error while accessing nbgrader configuration file.')

        start = content.find('c.NbGrader.course_titles')
        end = content.find('}', start)
        pre = content[:start]
        code = content[start:end + 1]
        post = content[end + 1:]
        code = code.replace('c.NbGrader.course_titles = ', 'mapping.update(')
        code = code.replace('}', '})')

        mapping = {}
        exec(code + '\n')
        mapping[course_id] = course_title

        try:
            with open(file=nbgrader_config_path, mode='w') as nbgrader_config_file:
                nbgrader_config_file.write(pre)
                nbgrader_config_file.write(f'c.NbGrader.course_titles = {str(mapping)}')
                nbgrader_config_file.write(post)
        except (FileNotFoundError, PermissionError, OSError):
            logging.error('Error while accessing nbgrader configuration file.')

    # Add student to course.
    if grader_exists and not is_instructor:

        # Add student to nbgrader database.
        with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
            gb.update_or_create_student(
                username,
                first_name=auth_state.get('given_name', 'none'),
                last_name=auth_state.get('family_name', 'none'),
                email=auth_state.get('email', 'none'),
                lms_user_id=auth_state['sub']
            )

        # Add student to course's JupyterHub group, which is required by nbgrader.
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

# Grant permissions of user to its single-user server (else course list extension cannot read service list).
c.JupyterHub.load_roles.append({
    'name': 'server',
    'scopes': ['inherit'],
})

# Kore service definition.
c.JupyterHub.services.append({
    'name': 'kore',
    'url': 'http://127.0.0.1:10001',
    'display': True,
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

# Load autogenerated services.
load_subconfig(autogenerated_file_path)  # noqa