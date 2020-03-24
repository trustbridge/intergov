import sys
import os
import logging
import json
import datetime
from intergov.json_log_formatter import JsonFormatter, JsonEncoder


def _create_test_record(**kwargs):
    standard_formatter = logging.Formatter()
    record = logging.LogRecord(
        kwargs['name'],
        kwargs['level'],
        kwargs['pathname'],
        kwargs['lineno'],
        kwargs['msg'],
        kwargs['args'],
        kwargs['exc_info'],
        kwargs.get('func'),
        kwargs.get('sinfo')
    )

    msg = kwargs['msg']

    expected = {
        'name': kwargs['name'],
        'filename': kwargs['filename'],
        'module': __name__,
        'levelname': logging.getLevelName(kwargs['level'])
    }

    if isinstance(msg, dict):
        msg = json.loads(json.dumps(msg, cls=JsonEncoder))
        expected.update(msg)
        expected['message'] = None
    else:
        expected['message'] = record.getMessage()

    func_name = kwargs.get('func')
    if func_name:
        expected['funcName'] = func_name
    exc_info = kwargs['exc_info']
    if exc_info:
        expected['exc_info'] = standard_formatter.formatException(kwargs['exc_info'])
    exc_text = kwargs.get('exc_text')
    if exc_text:
        record.exc_text = exc_text
        expected['exc_info'] = exc_text

    return record, expected


def test():
    # test initialization
    formatter = JsonFormatter()

    # test formatting
    test_exception = Exception('Hi')
    try:
        raise test_exception
    except Exception:
        exc_info = sys.exc_info()

    record, expected_output_dict = _create_test_record(
        name='testLoggerName',
        func='test_logger',
        level=logging.INFO,
        exc_info=exc_info,
        msg="Hello %s",
        args=("world",),
        lineno=0,
        filename=os.path.basename(__file__),
        pathname=os.path.abspath(__file__)
    )
    json_value_dict = json.loads(formatter.format(record))
    assert json_value_dict == expected_output_dict

    # {
    #     "exc_info": "Traceback (most recent call last):\n  File \"/src/tests/unit/test_json_log_formatter.py\...
    #     "filename": "test_json_log_formatter.py",
    #     "funcName": "test_logger",
    #     "levelname": "INFO",
    #     "message": "Hello world",
    #     "module": "test_json_log_formatter",
    #     "msg": "Hello %s",
    #     "name": "testLoggerName"
    # }

    class Unstringifiable(object):
        def __str__(self):
            raise TypeError("Haha")

    msg = {
        'test': 'test message',
        'now': datetime.datetime.utcnow(),
        'exception': test_exception,
        'traceback': exc_info[2],
        'willbenone': Unstringifiable()
    }

    out_msg = json.loads(json.dumps(msg, cls=JsonEncoder))
    for key, item in msg.items():
        if key != 'willbenone':
            assert out_msg[key] is not None
        else:
            assert out_msg[key] is None

    record, expected_output_dict = _create_test_record(
        name='testLoggerName',
        func='test_logger',
        level=logging.INFO,
        exc_info=None,
        exc_text=str(test_exception),
        msg=msg,
        args=tuple(),
        lineno=0,
        filename=os.path.basename(__file__),
        pathname=os.path.abspath(__file__)
    )
    json_value_dict = json.loads(formatter.format(record))
    assert json_value_dict == expected_output_dict

    # Output example
    # {
    #     "exc_info": "Hi",
    #     "exception": "Hi",
    #     "filename": "test_json_log_formatter.py",
    #     "funcName": "test_logger",
    #     "levelname": "INFO",
    #     "message": null,
    #     "module": "test_json_log_formatter",
    #     "name": "testLoggerName",
    #     "now": "2019-06-23T12:52:23.722412",
    #     "test": "test message",
    #     "traceback": "File \"/src/tests/unit/test_json_log_formatter.py\", line 64, in ...
    #     "willbenone": null
    # }
