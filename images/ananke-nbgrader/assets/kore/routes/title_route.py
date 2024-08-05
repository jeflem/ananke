import json
import logging

from flask import Blueprint, Response
from flask import request as flask_request

from models.lti_file_reader import LTIFileReader

title_bp = Blueprint('title', __name__)


@title_bp.route('/title', methods=['GET'])
def title():
    try:
        user_name = flask_request.args.get('user')
        logging.debug(f'User: {user_name}')
    except KeyError:
        logging.error('Request key is not in form!')
        return Response(response=json.dumps({'message': 'KeyError'}), status=500)

    logging.info(f'User {user_name} is accessing title of courses.')

    # Read and parse JSON file containing LTI data of current user.
    lti_file_reader: LTIFileReader = LTIFileReader(user_name=user_name, file_path=f'runtime/lti_{user_name}.json')
    lti_file_reader.read_file()
    lti_file_reader.extract_values()

    if lti_file_reader.read_success and lti_file_reader.parse_success:
        course_id, course_title = lti_file_reader.course_id, lti_file_reader.course_title
    else:
        return lti_file_reader.error_response

    return Response(response=json.dumps({'message': 'Title successfully retrieved.', 'title': course_title.removesuffix(f' ({course_id})')}), status=200)
