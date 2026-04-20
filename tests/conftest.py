import pytest

import app as fieldsense_app_module


@pytest.fixture
def client():
    app = fieldsense_app_module.app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
