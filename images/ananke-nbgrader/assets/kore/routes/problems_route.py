import json
import logging
import time
from pathlib import Path
from subprocess import run, CalledProcessError

from flask import Blueprint, Response, current_app
from flask import request as flask_request

from exceptions import InfoFileError
from misc.utils import get_list, load_info
from models.enums import Content

problems_bp = Blueprint('problems', __name__)


@problems_bp.route('/problems', methods=['GET', 'POST'])
def problems():
    config_loader = current_app.config['CONFIG_LOADER']

    autogenerated_file_path = config_loader.autogenerated_file_path
    date_time_format = config_loader.date_time_format

    # Retrieve full problem list (active and backed up ones).
    if flask_request.method == 'GET':
        try:
            return get_list(autogenerated_file_path=autogenerated_file_path, content=Content.PROBLEMS)
        except ValueError:
            return Response(response=json.dumps({'message': 'ValueError'}), status=500)

    # Copy a problem.
    if flask_request.method == 'POST':
        try:
            src = flask_request.json['fromPath'].removesuffix('/')
            dst = flask_request.json['toPath'].removesuffix('/')
        except KeyError:
            logging.error('Request key is not in form!')
            return Response(response=json.dumps({'message': 'KeyError'}), status=500)

        # Read `info.json` file.
        try:
            info = load_info(f'{dst}/info.json')
            grader_user = info['grader_user']
        except (KeyError, InfoFileError):
            return Response(response=json.dumps({'message': 'InfoFileError'}), status=500)

        dst = f'{dst}/source/imported/'
        filename = f'{Path(src).stem}_{time.strftime(date_time_format)}{Path(src).suffix}'
        try:
            run(['mkdir', '-p', dst], check=True)
            run(['cp', src, f'{dst}{filename}'], check=True)
            run(['chown', '-R', f'{grader_user}:{grader_user}', f'{dst}'], check=True)
        except CalledProcessError:
            return Response(response=json.dumps({'message': 'CalledProcessError'}), status=500)

        return Response(response=json.dumps({'message': 'Selected problem copied successfully! \n'
                                                        'Please refresh the webpage (Formgrader) to see the imported problem.'}), status=200)
