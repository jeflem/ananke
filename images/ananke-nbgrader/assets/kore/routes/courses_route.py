import grp
import json
import logging
import os
import time
from collections import Counter
from glob import glob
from string import capwords
from subprocess import run, CalledProcessError

import numpy as np
from flask import Response, Blueprint, current_app
from flask import request as flask_request
from nbgrader.api import Gradebook
from werkzeug.exceptions import BadRequestKeyError

from exceptions import AutogeneratedFileError
from misc.utils import get_hub_base_url, read_autogenerated_config, write_autogenerated_config
from models.lti_file_reader import LTIFileReader

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/courses', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def courses():
    config_loader = current_app.config['CONFIG_LOADER']

    autogenerated_file_path = config_loader.autogenerated_file_path
    date_time_format = config_loader.date_time_format

    kore_token = current_app.config['KORE_TOKEN']

    if flask_request.method == 'GET':
        try:
            user_name = flask_request.args.get('user')
            logging.debug(f'User: {user_name}')

        except BadRequestKeyError:
            logging.error('Request key is not in form!')
            return Response(response=json.dumps({'message': 'BadRequestKeyError'}), status=500)

        logging.info(f'User {user_name} is generating list of courses for copy.')

        # Read and parse JSON file containing LTI data of current user.
        lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
        lti_file_reader.read_file()
        lti_file_reader.extract_values()

        if lti_file_reader.read_success and lti_file_reader.parse_success:
            course_id, course_title, grader_user = lti_file_reader.course_id, lti_file_reader.course_title, lti_file_reader.grader_user
        else:
            return lti_file_reader.error_response

        # Access list of 'owned' groups, this is necessary to copy assignments stored at '/home/FORMGRADER_USER' and verifying access rights.
        try:
            _, _, groups = read_autogenerated_config(autogenerated_file_path=autogenerated_file_path)

        except AutogeneratedFileError:
            return Response(response=json.dumps({'message': 'AutogeneratedFileError'}), status=500)

        # TODO This is an optional feature where the problems of the course one is running in are NOT appended. This has to be evaluated, if it should stay or leave the code.
        #  Dependent on the decision the following code has to refactored.
        owned_groups = [group.lstrip('formgrade-') for group in groups if user_name in groups.get(group) and group.lstrip('formgrade-') != grader_user]
        base_paths = [item.path.removesuffix('/') for item in os.scandir('/home') if item.is_dir() and grp.getgrgid(os.stat(item.path).st_gid)[0] in owned_groups]
        logging.debug(f'Owned groups: {owned_groups}')
        logging.debug(f'Base paths: {base_paths}')

        # Get all paths of courses that are present and accessible. Due to possible sorting issues the list will be composed of to sub-lists which contain the paths for active
        # courses and the paths of backed up ones respectively.
        active_course_paths = []
        for base_path in base_paths:
            active_course_paths.extend(
                [course.removesuffix('/') for course in glob(pathname=f'{base_path}/course_data/source/') if glob(pathname=f'{course}**/*.ipynb', recursive=True)]
            )

        backed_up_course_paths = []
        backed_up_course_paths.extend(
            [course.removesuffix('/') for course in glob(pathname=f'/var/lib/private/{user_name}/*/source/') if glob(pathname=f'{course}**/*.ipynb', recursive=True)]
        )

        # Check if lists of course paths is empty. If that is the case return a message and status code indication just that.
        if not active_course_paths and not backed_up_course_paths:
            logging.error('No courses found that can be copied.')
            return Response(response=json.dumps({'message': 'NoContentFound'}), status=500)

        # Sort the lists and generate combined list.
        active_course_paths = sorted(active_course_paths)
        logging.debug(f'Sorted active course paths: {active_course_paths}')
        backed_up_course_paths = sorted(backed_up_course_paths)
        logging.debug(f'Sorted backed up course paths: {backed_up_course_paths}')
        course_paths = active_course_paths + backed_up_course_paths
        logging.debug(f'Resulting complete course paths: {course_paths}')

        # Generate names to display in the dropdown menu of the kore extension. This is done separately for both lists, which is necessary due to sorting problematic induced by the
        # appending of a string representing the origin of the course to be copied (name of the active course or backup for backed up ones) in interaction with the np.unique method
        # which returns a sorted list again, which may not be in original order.
        active_course_names = []
        for active_course_path in active_course_paths:
            split_string = active_course_path.split('/')
            info_file_path = f'/home/{split_string[2]}/info.json'

            try:
                # TODO refactor way of accessing, this may be simplified
                with open(file=info_file_path, mode='r') as info_file:
                    info = json.load(info_file)

            except FileNotFoundError:
                logging.error('Info file not found!')
                return Response(response=json.dumps({'message': 'FileNotFoundError'}), status=500)

            except PermissionError:
                logging.debug('Info file not readable!')

                try:
                    logging.debug('Trying to change permission of info file!')
                    logging.debug(f'Executing chmod 600 {info_file_path}')
                    run(['chmod', '600', info_file_path], check=True)

                    with open(file=info_file_path, mode='r') as info_file:
                        info = json.load(info_file)

                except CalledProcessError:
                    logging.error('Command cannot be executed!')
                    return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

            except OSError:
                logging.error('Info file can not be opened!')
                return Response(response=json.dumps({'message': 'OSError'}), status=500)

            active_course_names.append(info['title'])

        logging.debug(f'Active course names: {active_course_names}')

        backed_up_course_names = []
        for backed_up_course_path in backed_up_course_paths:
            split_string = backed_up_course_path.split('/')
            backed_up_course_names.append(f'{split_string[-2]} (Backup)')

        logging.debug(f'Backed up course names: {backed_up_course_names}')

        # Check if strings in lists are unique. This is done with the np.unique function, which returns a tuple consisting of arrays for sorted unique elements and counts of those
        # elements. If not rename non-unique values by appending a string in form of f' ({i})', where i is an integer representing the count of the occurrence. This is necessary
        # for the proper accessing of the path of the course to be copied in 'index.ts' of the kore-extension.
        unique_course_names = []
        for course_names in [active_course_names, backed_up_course_names]:
            unique_array, unique_count = np.unique(course_names, return_counts=True)

            if not np.all(unique_count == 1):
                counts = dict(Counter(course_names))
                course_names = [key if i == 0 else key + f' ({i})' for key in unique_array for i in range(counts[key])]

            course_names = [capwords(name.replace('_', ' ')) for name in course_names]
            unique_course_names.extend(course_names)

        logging.debug(f'Unique course names: {unique_course_names}')

        course_list = {
            'message': 'List of courses successfully retrieved.',
            'names': unique_course_names,
            'paths': course_paths
        }
        logging.info(f'Generated course list: {course_list}')

        return Response(response=json.dumps(course_list), status=200)

    if flask_request.method == 'POST':
        try:
            user_name, path = flask_request.json['user'], flask_request.json['path'].removesuffix('/')
            logging.debug(f'User: {user_name}')
            logging.debug(f'Path of course to be copied: {path}')

        except BadRequestKeyError:
            logging.error('Request key is not in form!')
            return Response(response=json.dumps({'message': 'BadRequestKeyError'}), status=500)

        logging.info(f'User {user_name} is copying course from {path}.')

        # Read and parse JSON file containing LTI data of current user.
        lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
        lti_file_reader.read_file()
        lti_file_reader.extract_values()

        if lti_file_reader.read_success and lti_file_reader.parse_success:
            course_id, course_title, grader_user = lti_file_reader.course_id, lti_file_reader.course_title, lti_file_reader.grader_user
        else:
            return lti_file_reader.error_response

        # Generate list of assignments present in the course chosen.
        assignments = [assignment.removesuffix('/') for assignment in glob(pathname=f'{path}/*/') if glob(pathname=f'{assignment}/**/*.ipynb', recursive=True)]

        # Check if the .../source/ folder for the grader user is present otherwise create it.
        source_folder = f'/home/{grader_user}/course_data/source/'
        if not os.path.isdir(source_folder):
            try:
                logging.debug(f'Executing: mkdir -p {source_folder}')
                run(['mkdir', '-p', source_folder], check=True)

            except CalledProcessError:
                logging.error('Command cannot be executed!')
                return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        for assignment in assignments:
            # Get name of assignment to be copied.
            assignment_name = assignment.split('/')[-1]
            actual_time = time.strftime(date_time_format)
            logging.debug(f'Assignment name: {assignment_name}')
            logging.debug(f'Actual time: {actual_time}')

            # Copy assignment and change ownership.
            src = f'{assignment}/'
            dst = f'/home/{grader_user}/course_data/source/{assignment_name} ({actual_time})/'

            try:
                logging.debug(f'Executing: cp -r {src} {dst}')
                run(['cp', '-r', src, dst], check=True)
                logging.debug(f'Executing: chown -R {grader_user}:{grader_user} {dst}')
                run(['chown', '-R', f'{grader_user}:{grader_user}', dst], check=True)

            except CalledProcessError:
                logging.error('Command cannot be executed!')
                return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        return Response(response=json.dumps({'message': 'Selected course copied successfully! \n'
                                                        'Please refresh the webpage (Formgrader) to see the imported course.'}), status=200)

    if flask_request.method == 'PUT':
        try:
            user_name = flask_request.json['user']
            logging.debug(f'User: {user_name}')

        except BadRequestKeyError:
            logging.error('Request key is not in form!')
            return Response(response=json.dumps({'message': 'BadRequestKeyError'}), status=500)

        logging.info(f'User {user_name} is backing up current course.')

        # Read and parse JSON file containing LTI data of current user.
        lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
        lti_file_reader.read_file()
        lti_file_reader.extract_values()

        if lti_file_reader.read_success and lti_file_reader.parse_success:
            course_id, course_title, grader_user = lti_file_reader.course_id, lti_file_reader.course_title, lti_file_reader.grader_user
        else:
            return lti_file_reader.error_response

        # Backup of current course.
        actual_time = time.strftime(date_time_format)
        src = f'/home/{grader_user}/course_data/'
        dst = f'/var/lib/private/{user_name}/{course_title.removesuffix(f" ({course_id})")} ({actual_time})/'

        try:
            logging.debug(f'Executing: cp -r {src} {dst}')
            run(['cp', '-r', src, dst], check=True)
            logging.debug(f'Executing: chown -R {user_name}:{user_name} {dst}')
            run(['chown', '-R', f'{user_name}:{user_name}', dst], check=True)

        except CalledProcessError:
            logging.error('Command cannot be executed!')
            return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        return Response(response=json.dumps({'message': 'Selected course backed up successfully!'}), status=200)

    if flask_request.method == 'PATCH':
        try:
            user_name = flask_request.json['user']
            logging.debug(f'User: {user_name}')

        except BadRequestKeyError:
            logging.error('Request key is not in form!')
            return Response(response=json.dumps({'message': 'BadRequestKeyError'}), status=500)

        logging.info(f'User {user_name} is resetting current course.')

        # Read and parse JSON file containing LTI data of current user.
        lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
        lti_file_reader.read_file()
        lti_file_reader.extract_values()

        if lti_file_reader.read_success and lti_file_reader.parse_success:
            lti_state = lti_file_reader.lti_state
            course_id, course_title, grader_user = lti_file_reader.course_id, lti_file_reader.course_title, lti_file_reader.grader_user
        else:
            return lti_file_reader.error_response

        # Remove students from gradebook.
        with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
            usernames = [student.id for student in gb.students]
            for username in usernames:
                gb.remove_student(username)

        # Remove students from courses nbgrader group.
        base_url = get_hub_base_url(lti_state)
        logging.debug(f'Removing all students from nbgrader group of course {course_id}.')
        # TODO add check=True
        # TODO add a custom error?
        run(['systemd-run', 'curl',
             '-H', 'Content-Type: application/json',
             '-H', 'Accept: application/json',
             '-H', f'Authorization: token {kore_token}',
             '-X', 'DELETE',
             '-d', '{"users":' + json.dumps(usernames) + '}',
             f'http://127.0.0.1:8081/{base_url}hub/api/groups/nbgrader-{course_id}/users'])

        # Clean up the nbgrader exchange directory.
        try:
            logging.debug(f'Executing: rm -rf /opt/nbgrader_exchange/{course_id}/')
            run(['rm', '-rf', f'/opt/nbgrader_exchange/{course_id}/'], check=True)

        except CalledProcessError:
            logging.error('Command cannot be executed!')
            return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        # Clean up course directory.
        try:
            logging.debug(f'Executing: rm /home/{grader_user}/course_data/gradebook.db')
            run(['rm', f'/home/{grader_user}/course_data/gradebook.db'], check=True)

        except CalledProcessError:
            logging.error('Command cannot be executed!')
            return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        for directory in ['autograded', 'feedback', 'release', 'submitted']:
            try:
                logging.debug(f'Executing: rm -rf /home/{grader_user}/course_data/{directory}/')
                run(['rm', '-rf', f'/home/{grader_user}/course_data/{directory}/'], check=True)

            except CalledProcessError:
                logging.error('Command cannot be executed!')
                return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        return Response(response=json.dumps({'message': 'Selected course reset successfully!'}), status=200)

    # TODO: Change code so that deletion of course is done by a list of available courses where the user has permissions for.
    #  This will make it possible to delete courses where the corresponding course on LMS side was deleted already.
    if flask_request.method == 'DELETE':
        try:
            user_name = flask_request.json['user']
            logging.debug(f'User: {user_name}')
        except BadRequestKeyError:
            logging.error('Request key is not in form!')
            return Response(response=json.dumps({'message': 'BadRequestKeyError'}), status=500)

        logging.info(f'User {user_name} is deleting current course.')

        # Read and parse JSON file containing LTI data of current user.
        lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
        lti_file_reader.read_file()
        lti_file_reader.extract_values()

        if lti_file_reader.read_success and lti_file_reader.parse_success:
            course_id, course_title, grader_user = lti_file_reader.course_id, lti_file_reader.course_title, lti_file_reader.grader_user
        else:
            return lti_file_reader.error_response

        # Get user's courses and corresponding information.
        try:
            services, roles, groups = read_autogenerated_config(autogenerated_file_path=autogenerated_file_path)
        except AutogeneratedFileError:
            return Response(response=json.dumps({'message': 'AutogeneratedFileError'}), status=500)

        # Access group and delete it from groups list.
        group = groups.get(f'formgrade-{course_id}')
        if not group:
            logging.error('Group not found in autogenerated configuration file!')
            return Response(response=json.dumps({'message': 'GroupNotFoundError'}), status=500)

        del groups[f'formgrade-{course_id}']
        logging.debug(f'Removed group for course {course_id}!')

        # Delete roles from roles lists.
        for role in roles:
            if role.get('name') == f'formgrader-{course_id}-role':
                del roles[roles.index(role)]
                logging.debug(f'Removed role for course {course_id}!')
            if role.get('name') == 'formgrader-service-role':
                del role['services'][role['services'].index(course_id)]

        # Delete services from services list.
        for service in services:
            if service['name'] == course_id:
                del services[services.index(service)]
                logging.debug(f'Removed service {course_id}!')
                break

        # Write resulting configuration file.
        try:
            write_autogenerated_config(autogenerated_file_path=autogenerated_file_path, services=services, roles=roles, groups=groups)
        except AutogeneratedFileError:
            return Response(response=json.dumps({'message': 'AutogeneratedFileError'}), status=500)

        # Delete nbgrader exchange directory for course.
        try:
            logging.debug(f'Removing nbgrader exchange for course {course_id}!')
            run(['rm', '-rf', f'/opt/nbgrader_exchange/{course_id}/'], check=True)
        except CalledProcessError:
            logging.error('Command cannot be executed!')
            return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        # Delete grader user for course.
        try:
            logging.debug(f'Removing grader user for course {course_id}!')
            run(['userdel', f'{grader_user}'], check=True)
            run(['rm', '-rf', f'/home/{grader_user}/'], check=True)
        except CalledProcessError:
            logging.error('Command cannot be executed!')
            return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        # Generate new nbgrader configuration code and write it to file.
        with open(file='/opt/conda/envs/jhub/etc/jupyter/nbgrader_config.py') as nb_grader_config:
            content = nb_grader_config.read()
        start = content.find('c.NbGrader.course_titles')
        end = content.find('}', start)
        pre = content[:start]
        code = content[start:end + 1]
        post = content[end + 1:]
        code = code.replace('c.NbGrader.course_titles = ', 'mapping.update(')
        code = code.replace('}', '})')
        mapping = {}
        exec(code + '\n')

        if course_id in mapping.keys():
            del mapping[course_id]

        with open(file='/opt/conda/envs/jhub/etc/jupyter/nbgrader_config.py', mode='w') as nb_grader_config:
            nb_grader_config.write(pre)
            nb_grader_config.write(f'c.NbGrader.course_titles = {str(mapping)}')
            nb_grader_config.write(post)

        # Restart JupyterHub to adopt the changes.
        logging.info('Restarting JupyterHub in 3 seconds...')
        run(['systemd-run', '--on-active=3', 'systemctl', 'restart', 'jupyterhub'])

        return Response(response=json.dumps({'message': 'Selected course deleted successfully! JupyterHub will restart soon!'}), status=200)
