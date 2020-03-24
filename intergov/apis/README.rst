README(Draft)
=============

This is a raw version of readme containing basic information about APIs.

ERRORS
------

Errors response
***************

Each API endpoint may return error response if used incorrectly or if internal errors occur.
Error response follows `jsonapi standard`_.

.. _`jsonapi standard`: https://jsonapi.org/format/#errors

**Format:**

.. code-block:: json

  {
    "errors":[]
  }

**errors** is a list of errors which API returns during call. Contains one or more **error items**.

Error item
**********

Each error item represents exception/error raised during a call.

**Format:**

.. code-block:: json

  {
    "status": "Not Found",
    "code": "generic-http-error",
    "title": "Not Found",
    "detail": "Requested resource not found",
    "source": [
        {
          "KeyError": "document key"
        }
    ]
  }


#. ``Static`` ``String`` **status** - human readable representation of the response status code. Format is standard_ string representation of HTTP status code.
#. ``Static`` ``String`` **code** - application specific error code. Default format is error class name.
#. ``Static`` ``String`` **title** - human readable error title. Default format is error class name.
#. ``Dynamic`` ``String`` **detail** - human readable error details. Has no strict format.
#. ``Dynamic`` ``List`` **source** - machine friendly error details. Has no strict format.

.. _standard: https://tools.ietf.org/html/rfc7231#page-48

.. important::

  **detail** and **source** keys must only be present together, not separately.
  Because they are two different representation of the same thing, error details.
  In case when one of them not needed it must be empty but present in the error.
  **Example:**

  .. code-block:: json

    {
      "details": "We need details, but not source",
      "source": []
    }

.. important::

  ``Integer`` HTTP Response status:
    #. ``if errors.length > 1 then response.status = 400 #Bad Request``
    #. ``if errors.length == 1 then response.status = errors[0].status # Integer representation``
