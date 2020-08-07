Document API
============

Requires authentication. Auth says if the user is legal entity in local jurisdiction,
foreign jurisdiction, authorized application and so on. Please note that `document` and `object`
is the same thing here. Message has `obj` field, which contains multihash of the uploaded
file, which is called `object` or `document` in different places. It's just a some
content, which may be JSON, ZIP, PDF document or something else. Read the EDI3 specification for details about the documents inner format, it's not important for the document API itself.

``docs/_build/html/intergov/components.html#document-api``

Auth:
* demo only - JWTBODY - just pass the JWT payload, unsigned, to the application
  + ``Authorization: JWTBODY {"sub": "documents-api", "party": "spider", "jurisdiction": "AU"}``
  + parties may be "spider", "app" (chambers or importers) and so on
  + other fields may be present
  + ``jurisdiction`` is the most important and used to allow or deny the access
* OIDC - use standard OIDC protocol and add meaningful fields to the JWT
  + must provide at least jurisdiction, given our documents are shared on jurisdiction basis

Endpoints
---------

Post document
*************

Must be a multipart/form-data request with single file provided.

URL is `/jurisdictions/{receiver}/`

Response is multihash of the file uploaded. Client may calculate the multihash itself and compare
it with the returned one to ensure no data corruption occured. We use sha256 as the hash function.

No extra parameters are supported currently, but they may be provided as POST request (for backwards
compatibility with current API version and future clients).

    curl -XPOST http://127.0.0.1:5103/jurisdictions/US \
         -S -F "someextra=parameter" -F "file=@img.jpg;type=image/jpg" \
         -H "Accept: application/json"

Response is a json dict with `multihash` parameter (may contain more data in future versions)

	{"multihash": "QmdywW1TrEYgCHuoTkPn4a7JY3MTJu3gWbhHCy2awD1ZfU"}

Errors
******

#. Unsupported Media Type Error => Generic HTTP Error => Unsupported Media Type
#. Bad Country Name Error
#. No Input File Error
#. Too Many Files Error
#. Generic HTTP Error
#. Internal Server Error


Retrieve document
*****************

Document retrieving party must have access to it (be either sender or receiver).

The whole file binary content will be returned. Please note original filename (of the uploaded document)
is not preserved due to security and simplification reasons.

``curl -XGET http://127.0.0.1:5103/QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n``

``curl -XGET http://127.0.0.1:5103/QmdywW1TrEYgCHuoTkPn4a7JY3MTJu3gWbhHCy2awD1ZfU \
    --output downloaded_file.jpeg``

Errors
******
#. Bad Country Name Error
#. Document Not Found => Generic HTTP Error => Not Found
#. Generic HTTP Error
#. Internal Server Error
