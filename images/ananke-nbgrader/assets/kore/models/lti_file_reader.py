import hashlib
import json
import logging
from typing import Optional

from flask import Response


class LTIFileReader:
    def __init__(self, user_name: str, file_path: str) -> None:
        self.user_name: str = user_name
        self.file_path: str = file_path
        self.lti_state: Optional[dict] = None
        self.read_success: bool = False
        self.course_id: Optional[str] = None
        self.course_title: Optional[str] = None
        self.grader_user: Optional[str] = None
        self.parse_success: bool = False
        self.error_response: Optional[Response] = None
        self.preflight_error: Optional[str] = None

    def read_file(self) -> None:
        try:
            with open(self.file_path, 'r') as file:
                # Check if the file has a JSON extension otherwise raise an error.
                if not self.file_path.lower().endswith('.json'):
                    raise ValueError('File is not a JSON file.')

                # Read content of file and set boolean value to True if reading is successful.
                self.lti_state = json.load(file)
                self.read_success = True
        except FileNotFoundError:
            logging.error(f'LTI state file for user {self.user_name} not found!')
            self.error_response = Response(response=json.dumps({'message': 'FileNotFoundError'}), status=404)
            self.preflight_error = 'LTI file for current user could not be found. Contact administrator or see logs for more details.'
        except PermissionError:
            logging.error(f'LTI state file for user {self.user_name} not readable!')
            self.error_response = Response(response=json.dumps({'message': 'PermissionError'}), status=400)
            self.preflight_error = 'LTI file for current user could not be read. Contact administrator or see logs for more details.'
        except ValueError:
            logging.error(f'LTI state file is not a JSON!')
            self.error_response = Response(response=json.dumps({'message': 'ValueError'}), status=400)
            self.preflight_error = 'LTI file for current user is not a JSON file. Contact administrator or see logs for more details.'
        except OSError:
            logging.error(f'LTI state file for user {self.user_name} can not be opened!')
            self.error_response = Response(response=json.dumps({'message': 'OSError'}), status=500)
            self.preflight_error = 'LTI file for current user could not be opened. Contact administrator or see logs for more details.'

    def extract_values(self) -> None:
        if not self.read_success:
            return

        if not isinstance(self.lti_state, dict):
            logging.error('LTI state content is not a dict!')
            self.error_response = Response(response=json.dumps({'message': 'ContentError'}), status=500)
            return

        # Extract course id, course title and grader username from lti state.
        deployment_id = self.lti_state.get('https://purl.imsglobal.org/spec/lti/claim/deployment_id', '0')
        resource_link_id = self.lti_state.get('https://purl.imsglobal.org/spec/lti/claim/resource_link').get('id')
        resource_link_title = self.lti_state.get('https://purl.imsglobal.org/spec/lti/claim/resource_link').get('title')
        context_title = self.lti_state.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('title')

        h = hashlib.shake_256(f'{deployment_id}-{resource_link_id}'.encode())
        self.course_id = 'c-' + h.hexdigest(8)
        self.grader_user = self.course_id[0:32]

        if resource_link_title and context_title:
            course_title = f'{context_title} - {resource_link_title}'
        elif resource_link_title:
            course_title = resource_link_title
        elif context_title:
            course_title = context_title
        else:
            course_title = 'No title available'
        self.course_title = f'{course_title} ({self.course_id})'.replace('\'', '')

        logging.debug(f'Course ID: {self.course_id}')
        logging.debug(f'Course title: {self.course_title}')
        logging.debug(f'Grader user: {self.grader_user}')
        self.parse_success = True
