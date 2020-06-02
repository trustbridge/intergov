from intergov.conf import env_json


class Config(object):
    # configuration for domain module, may mix some different
    # things like Countries and wire protocols, so once is starts to be
    # disturbing we may split it further.
    DOCUMENT_REPOS = env_json(
        "IGL_COUNTRY_DOCUMENT_REPORTS",
        default=env_json(
            "IGL_CONTRY_DOCUMENT_REPORTS", default={
                'AU': 'http://127.0.0.1:7770/documents/',
                'CN': 'http://127.0.0.1:7771/documents/',
                'NZ': 'http://127.0.0.1:7782/documents/',
                'SG': 'http://127.0.0.1:7784/documents/',
            }
        )
    )
