import json
from functools import wraps

from flask import request
from werkzeug.exceptions import Unauthorized

from intergov.loggers import logging

logger = logging.getLogger(__name__)


def demo_auth(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '').strip()
            if not auth_header:
                raise Unauthorized("Unknown or no auth")
            if not auth_header.startswith("JWTBODY"):
                raise Unauthorized("Unknown or no auth")
            jwtbody_content = auth_header[len("JWTBODY"):][:2048]
            try:
                jwtbody = json.loads(jwtbody_content)
            except Exception:
                raise Unauthorized("Invalid auth format")
            request.auth = jwtbody
            role = jwtbody.get('role')
            if roles:
                if not role or role not in roles:
                    raise Unauthorized()
            return f(*args, **kwargs)
        return wrapped
    return wrapper
