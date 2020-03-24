from unittest import mock
from intergov.processors.obj_spider import ObjectSpider


@mock.patch('intergov.processors.obj_spider.Country')
@mock.patch('intergov.processors.obj_spider.ObjectACLRepo')
@mock.patch('intergov.processors.obj_spider.ObjectRetrievalRepo')
@mock.patch('intergov.processors.obj_spider.ObjectLakeRepo')
@mock.patch('intergov.processors.obj_spider.RetrieveAndStoreForeignDocumentsUseCase')
def test(
    RetrieveAndStoreForeignDocumentsUseCase,
    ObjectLakeRepo,
    ObjectRetrievalRepo,
    ObjectACLRepo,
    Country
):
    spider = ObjectSpider()
    for Repo in [
        ObjectACLRepo,
        ObjectLakeRepo,
        ObjectRetrievalRepo
    ]:
        Repo.assert_called_once()
    RetrieveAndStoreForeignDocumentsUseCase.assert_called_once_with(
        country=Country.return_value,
        object_lake_repo=ObjectLakeRepo.return_value,
        object_acl_repo=ObjectACLRepo.return_value,
        object_retrieval_repo=ObjectRetrievalRepo.return_value
    )

    use_case = RetrieveAndStoreForeignDocumentsUseCase.return_value
    use_case.execute.side_effect = [
        True,
        False,
        None,
        Exception()
    ]
    assert iter(spider) is spider
    assert next(spider) is True
    assert next(spider) is False
    assert next(spider) is None
    assert next(spider) is None
