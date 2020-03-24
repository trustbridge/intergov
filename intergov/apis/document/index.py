import json
import os

from flask import (
    Blueprint, Response,
)

from intergov.monitoring import statsd_timer


blueprint = Blueprint('index', __name__)


@blueprint.route('/', methods=['GET'])
@statsd_timer("api.document.endpoint.index_page")
def index_page():
    return Response(
        json.dumps({
            "service": os.path.dirname(os.path.realpath(__file__)).split('/')[-1],
        }),
        mimetype='application/json',
        status=200
    )
