import json
import os

from flask import (
    Blueprint, Response,
)


blueprint = Blueprint('index', __name__)


@blueprint.route('/', methods=['GET'])
def index_page():
    return Response(
        json.dumps({
            "service": os.path.dirname(os.path.realpath(__file__)).split('/')[-1],
        }),
        mimetype='application/json',
        status=200
    )
