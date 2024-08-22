import datetime
import json
import logging
import os
import time
from json import JSONDecodeError

import jwt
import requests
from flask import Blueprint, Response, current_app
from flask import request as flask_request
from nbgrader.api import Gradebook
from requests.exceptions import ConnectionError, HTTPError, RequestException
from urllib3.exceptions import LocationParseError

from exceptions import InfoFileError
from misc.utils import load_info

grades_bp = Blueprint('grades', __name__)


@grades_bp.route('/grades', methods=['POST'])
def grades():
    config_loader = current_app.config['CONFIG_LOADER']
    lti_config = config_loader.lti_config

    kore_token = current_app.config['KORE_TOKEN']

    if flask_request.method == 'POST':
        try:
            user_name = flask_request.json['user']
            path = flask_request.json['path'].removesuffix('/')
        except KeyError:
            return Response(response=json.dumps({'message': 'KeyError'}), status=500)

        logging.info(f'User {user_name} indents to send grades of course at {path}.')

        # Read `info.json` file.
        try:
            info = load_info(f'{path}/info.json')
            base_url = info['target_link_uri']
            aud = info['aud']
            lineitem = info['lineitem']
            grader_user = info['grader_user']
        except (KeyError, InfoFileError):
            return Response(response=json.dumps({'message': 'InfoFileError'}), status=500)

        # Get admin state.
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'token {kore_token}',
        }

        try:
            response = requests.get(url=f'http://127.0.0.1:8081/{base_url}hub/api/users/{user_name}', headers=headers)
            response.raise_for_status()
            user_data = response.json()
            admin = user_data['admin']
            logging.debug(f'{user_name} is admin: {admin}')
        except (HTTPError, LocationParseError, JSONDecodeError):
            logging.error(f'Error while trying to access admin state of user {user_name}!')
            return Response(response=json.dumps({'message': 'AdminStateError'}), status=500)

        # Create token for requesting access token from LMS.
        try:
            auth_token_request_data = {
                'iss': aud,
                'aud': lti_config['issuer'],
                'sub': aud,
                'iat': int(time.time()) - 5,
                'exp': int(time.time()) + 60,
            }
        except KeyError:
            logging.error('At least one key not found in LTI configuration or LTI state file!')
            return Response(response=json.dumps({'message': 'TokenCreationError'}), status=500)

        # Read the private key of Kore.
        private_key_path = 'keys/lti_key'
        try:
            with open(file=private_key_path, mode='r') as private_key:
                private_key = private_key.read()
        except (FileNotFoundError, PermissionError, OSError):
            logging.error('Error while handling private key!')
            return Response(response=json.dumps({'message': 'PrivateKeyError'}), status=500)

        # Read the public key of Kore.
        public_key_path = 'keys/lti_key.json'
        try:
            with open(file=public_key_path, mode='r') as public_key:
                jwk = json.load(public_key)
        except (FileNotFoundError, PermissionError, OSError, JSONDecodeError):
            logging.error('Error while handling public key!')
            return Response(response=json.dumps({'message': 'PublicKeyError'}), status=500)

        token = jwt.encode(auth_token_request_data, private_key, algorithm='RS256', headers={'kid': jwk['kid']})
        params = {
            'grant_type': 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': token,
            'scope': 'https://purl.imsglobal.org/spec/lti-ags/scope/score https://purl.imsglobal.org/spec/lti-ags/scope/lineitem'
        }

        # Retrieve access token from LMS.
        try:
            response = requests.post(lti_config['access_token_url'], data=params)
            response.raise_for_status()
            access_token = response.json()['access_token']
        except (KeyError, HTTPError, LocationParseError, JSONDecodeError):
            logging.error('Error while accessing token.')
            return Response(response=json.dumps({'message': 'AccessTokenError'}), status=500)

        # Get score URL from line items.
        try:
            url, args = lineitem.split('?')
            score_url = url + '/scores?' + args
        except (ValueError, AttributeError):
            logging.error('Error while composing url for score sending!')
            return Response(response=json.dumps({'message': 'LineitemError'}), status=500)

        # Get parameters from gradebook.
        student_ids, scores, max_scores = [], [], []

        # Due to the fact that the gradebook.db would be created while trying to access it with the Gradebook() code line we have to check here if it exists
        if not os.path.isfile(f'/home/{grader_user}/course_data/gradebook.db'):
            logging.error('Gradebook does not exist!')
            return Response(response=json.dumps({'message': 'GradebookNotExistentError'}), status=500)

        with Gradebook(f'sqlite:////home/{grader_user}/course_data/gradebook.db') as gb:
            for student in gb.students:
                student_ids.append(student.lms_user_id)
                scores.append(student.score)
                max_scores.append(student.max_score)

        # Prepare user independent score data for sending.
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

        # Send scores to LMS.
        for student_id, score, max_score in zip(student_ids, scores, max_scores):
            params['userId'] = student_id
            params['scoreGiven'] = score
            params['scoreMaximum'] = max_score

            try:
                response = requests.post(score_url, json=params, headers=headers)
                response.raise_for_status()
                if response.status_code == 200:
                    logging.debug(f'Score(s) for student with ID {student_id} successfully send!')
            except (HTTPError, ConnectionError, RequestException):
                logging.error('Error while trying to send grades to LMS')
                return Response(response=json.dumps({'message': 'SendGradesError'}), status=500)

        return Response(response=json.dumps({'message': 'Grades send successfully!'}), status=200)
