import uuid

from intergov.domain import uri as u


def _generate_OK_URI_list():
    return (
        # Http
        "https://google.com/%s" % (uuid.uuid4()),
        "https://github.com/mozilla/mozilla-django-oidc",
        "http://66.media.tumblr.com/93624bf218770b4adbf3b6b430dad28b/tumblr_ngoz83U59O1s02vreo1_400.gif",  # NOQA
        "https://www.google.com/search?source=hp&ei=EFLDXJSjDsGxkwWCn4Qo&q=tiny+cats&btnK=%D0%9F%D0%BE%D0%B8%D1%81%D0%BA+%D0%B2+Google&oq=tiny+cats&gs_l=psy-ab.3..0i19l5j0i10i19j0i19l4.1405.2574..3031...0.0..0.168.924.9j1......0....1..gws-wiz.....0..0j0i10j0i22i30.G3y4rm0MhD0",  # NOQA
        # IPFS
        "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
        "/ipfs/QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4",
        "QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4",
        "zb2rhe5P4gXftAwvA4eXQ5HJwsER2owDyS9sKaQRRVQPn93bA",  # new IPFS format
        # other
        # "%s@%s::%s" % (uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    )


def _generate_bad_URI_list():
    # TODO: add more bad UIs
    return (
        '123/',
        '/wiw.eiwe/',
        'hjiasfuydtuio',
        '',
        "/ipfs/Qmalalalaa",
        "UUUrhe5P4gXftAwvA4eXQ5HJwsER2owDyS9sKaQRRVQPn93bA",
        "//google.com/%s" % (uuid.uuid4()),
        b"7777",
        0,
        None,
        Exception(),  # an object passed :-)
        str,
    )


def test_URI_validation_OK():
    '''
    A URI can be:
    * a valid URL
    * a fully qualified discoverable name
    * an ipfs multihash or ipfs address
    '''
    for uristr in _generate_OK_URI_list():
        uri = u.URI(uristr)
        print(uri, uristr)
        assert uri.is_valid()


def test_URI_validation_bad():
    for uristr in _generate_bad_URI_list():
        uri = u.URI(uristr)
        print(uri, uristr)
        assert not uri.is_valid()


def test_is_valid_url():
    urlstr = "http://foo.com/bar"
    uri = u.URI(urlstr)
    assert uri.is_valid_url()


def test_is_valid_multihash():
    for mhstr in (
            "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
            "QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4"):
        # TODO: should the following string pass?
        # "zb2rhe5P4gXftAwvA4eXQ5HJwsER2owDyS9sKaQRRVQPn93bA"
        uri = u.URI(mhstr)
        assert uri.is_valid_multihash()


def test_is_valid_ipfs():
    for ipfsstr in (
            "/ipfs/QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4",
            "/ipfs/zb2rhe5P4gXftAwvA4eXQ5HJwsER2owDyS9sKaQRRVQPn93bA"):
        uri = u.URI(ipfsstr)
        assert uri.is_valid_ipfs()


def test_is_valid_fqn():
    for fqnstr in (
            "AU.fbe4ad86-8000-497d-a341-78ecd324fd6f.15502b9c-0cc3-4347-ab73-3ab9f93b91d5",
            "UN.CEFACT.Trade.CertificateOfOrigin.created",
            "1.2.3.4.5.6.7.8.9.10.11.12"): 
        uri = u.URI(fqnstr)
        assert uri.is_valid_fqn()


def test_is_not_valid_fqn():
    for fqnstr in (
            "AUfbe4ad86-8000-497d-a341-78ecd324fd6f15502b9c-0cc3-4347-ab73-3ab9f93b91d5",
            "UN.CEFACT",
            1,
            "AU:fbe4ad86-8000-497d-a341-78ecd324fd6f:15502b9c-0cc3-4347-ab73-3ab9f93b91d5",
            b"AU.fbe4ad86-8000-497d-a341-78ecd324fd6f.15502b9c-0cc3-4347-ab73-3ab9f93b91d5"
            ):
        uri = u.URI(fqnstr)
        assert not uri.is_valid_fqn()
