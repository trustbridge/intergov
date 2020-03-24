from intergov.conf import env_json


class Config(object):
    # configuration for domain module, may mix some different
    # things like Countries and wire protocols, so once is starts to be
    # disturbing we may split it further.
    DOCUMENT_REPOS = env_json("IGL_CONTRY_DOCUMENT_REPORTS", default={
        'AU': 'http://127.0.0.1:7770/documents/',
        'CN': 'http://127.0.0.1:7771/documents/',
        'JP': 'http://127.0.0.1:7773/documents/',
        'KR': 'http://127.0.0.1:7774/documents/',
        'TH': 'http://127.0.0.1:7775/documents/',
        'BN': 'http://127.0.0.1:7776/documents/',
        'MM': 'http://127.0.0.1:7777/documents/',
        'KH': 'http://127.0.0.1:7778/documents/',
        'ID': 'http://127.0.0.1:7779/documents/',
        'LA': 'http://127.0.0.1:7780/documents/',
        'MY': 'http://127.0.0.1:7781/documents/',
        'NZ': 'http://127.0.0.1:7782/documents/',
        'PH': 'http://127.0.0.1:7783/documents/',
        'SG': 'http://127.0.0.1:7784/documents/',
        'VN': 'http://127.0.0.1:7785/documents/',
        'US': 'http://127.0.0.1:7786/docs/',
        'ES': 'http://127.0.0.1:7787/documentos/',
        'SK': 'http://127.0.0.1:7788/dokumenty/',
        'GB': 'http://127.0.0.1:7789/documents/',
    })
