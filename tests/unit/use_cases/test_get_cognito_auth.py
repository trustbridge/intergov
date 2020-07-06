import datetime

import pytest
import responses
from freezegun import freeze_time

from intergov.use_cases.get_cognito_auth import GetCognitoAuthUseCase


@pytest.mark.usefixtures("mocked_responses")
class TestGetCognitoAuthUseCase:
    @freeze_time('2020-07-06 11:17')
    def test_get_jwt__when_token_exist_and_not_expired__should_return_token(self):
        use_case = GetCognitoAuthUseCase('client_id', 'client_secret', 'scope', 'https://token_endpoint.com')
        use_case._jwt = 'existing cached token'
        use_case._jwt_expires_at = datetime.datetime(2020, 7, 6, 12, 17)
        assert use_case.get_jwt() == 'existing cached token'

    @freeze_time('2020-07-06 11:17')
    def test_get_jwt__when_no_token__should_issue_new_token_and_return_it(self):
        self.mocked_responses.add(responses.POST, 'https://token_endpoint.com', json={
            'expires_in': 3600,
            'access_token': 'new token'
        })
        use_case = GetCognitoAuthUseCase('client_id', 'client_secret', 'scope', 'https://token_endpoint.com')
        assert use_case.get_jwt() == 'new token'
        assert use_case._jwt_expires_at == datetime.datetime(2020, 7, 6, 12, 16)

    @freeze_time('2020-07-06 11:17')
    def test_get_jwt__when_token_expired__should_issue_new_token_and_return_it(self):
        self.mocked_responses.add(responses.POST, 'https://token_endpoint.com', json={
            'expires_in': 100,
            'access_token': 'new token'
        })
        use_case = GetCognitoAuthUseCase('client_id', 'client_secret', 'scope', 'https://token_endpoint.com')
        use_case._jwt = 'old token'
        use_case._jwt_expires_at = datetime.datetime(2020, 7, 6, 11, 16)
        assert use_case.get_jwt() == 'new token'
