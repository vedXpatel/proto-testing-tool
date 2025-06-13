import io
import os
import json
import tempfile
import types
import pytest
from unittest import mock
from protobuf_with_test_data import app, ProtobufService, SAMPLE_PROTO_CONTENT
from protobuf_with_test_data import sample_users, sample_products
import importlib

# test_protobuf.py



@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def clean_sample_data():
    # Reset global data before each test
    sample_users.clear()
    sample_products.clear()

def test_get_users_empty(client):
    rv = client.get('/api/users')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'users' in data
    assert data['users'] == {}

def test_get_products_empty(client):
    rv = client.get('/api/products')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'products' in data
    assert data['products'] == {}

def test_create_user_json(client):
    user = {
        "name": "Alice",
        "age": 25,
        "email": "alice@example.com",
        "active": True,
        "tags": ["dev", "python"]
    }
    rv = client.post('/api/users', json=user)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['status'] == 'created'
    assert data['user']['name'] == "Alice"

def test_create_product_json(client):
    product = {
        "product_name": "Widget",
        "price": 10.5,
        "quantity": 3,
        "category": "Tools"
    }
    rv = client.post('/api/products', json=product)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['status'] == 'created'
    assert data['product']['product_name'] == "Widget"

def test_create_user_json_missing_data(client):
    rv = client.post('/api/users', json=None)
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data

def test_create_product_json_missing_data(client):
    rv = client.post('/api/products', json=None)
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data

def test_upload_proto_success(client):
    # Mock subprocess.run to simulate successful proto compilation
    with mock.patch('protobuf.subprocess.run') as mock_run:
        mock_run.return_value = types.SimpleNamespace(returncode=0, stderr='', stdout='')
        proto_content = SAMPLE_PROTO_CONTENT.encode('utf-8')
        data = {
            'proto_file': (io.BytesIO(proto_content), 'test.proto')
        }
        rv = client.post('/upload_proto', data=data, content_type='multipart/form-data')
        assert rv.status_code == 200
        resp = rv.get_json()
        assert resp['success'] is True
        assert resp['filename'] == 'test.proto'

def test_upload_proto_no_file(client):
    rv = client.post('/upload_proto', data={}, content_type='multipart/form-data')
    assert rv.status_code == 400
    resp = rv.get_json()
    assert 'error' in resp

def test_upload_proto_invalid_extension(client):
    data = {
        'proto_file': (io.BytesIO(b'bad'), 'bad.txt')
    }
    rv = client.post('/upload_proto', data=data, content_type='multipart/form-data')
    assert rv.status_code == 400
    resp = rv.get_json()
    assert 'error' in resp

def test_test_api_get_users(client):
    # Test /test_api for GET users
    payload = {
        "api_url": "http://localhost:8080/api/users",
        "message_type": "UserRequest",
        "protocol": "rest",
        "method": "GET",
        "custom_data": ""
    }
    with mock.patch('protobuf.requests.get') as mock_get:
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.json.return_value = {'users': {}}
        mock_get.return_value = mock_resp
        rv = client.post('/test_api', json=payload)
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success'] is True
        assert data['response']['status_code'] == 200

def test_test_api_post_json(client):
    # Test /test_api for POST users (REST/JSON)
    payload = {
        "api_url": "http://localhost:8080/api/users",
        "message_type": "UserRequest",
        "protocol": "rest",
        "method": "POST",
        "custom_data": json.dumps({
            "name": "Bob",
            "age": 22,
            "email": "bob@example.com",
            "active": True,
            "tags": ["test"]
        })
    }
    with mock.patch('protobuf.requests.post') as mock_post:
        mock_resp = mock.Mock()
        mock_resp.status_code = 201
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.json.return_value = {'id': 'user_1', 'status': 'created'}
        mock_post.return_value = mock_resp
        rv = client.post('/test_api', json=payload)
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success'] is True
        assert data['response']['status_code'] == 201

def test_test_api_post_protobuf(client):
    # Test /test_api for POST users (protobuf)
    payload = {
        "api_url": "http://localhost:8080/api/users",
        "message_type": "UserRequest",
        "protocol": "protobuf",
        "method": "POST",
        "custom_data": ""
    }
    with mock.patch('protobuf.requests.post') as mock_post:
        mock_resp = mock.Mock()
        mock_resp.status_code = 201
        mock_resp.headers = {'content-type': 'application/x-protobuf'}
        mock_resp.content = b'binary'
        mock_post.return_value = mock_resp
        # Also patch load_proto_module to return a mock message class
        with mock.patch('protobuf.ProtobufService.load_proto_module') as mock_load:
            # Dynamically import the compiled sample_pb2 if available
            # Otherwise, skip this test
            try:
                sample_pb2 = importlib.import_module('proto_compiled.sample_pb2')
            except Exception:
                pytest.skip("sample_pb2 not available for protobuf test")
            mock_load.return_value = (sample_pb2, None)
            rv = client.post('/test_api', json=payload)
            assert rv.status_code == 200
            data = rv.get_json()
            assert data['success'] is True
            assert data['response']['status_code'] == 201

def test_test_api_invalid_message_type(client):
    payload = {
        "api_url": "http://localhost:8080/api/users",
        "message_type": "NonExistentType",
        "protocol": "rest",
        "method": "POST",
        "custom_data": ""
    }
    rv = client.post('/test_api', json=payload)
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data

def test_test_api_invalid_custom_data(client):
    payload = {
        "api_url": "http://localhost:8080/api/users",
        "message_type": "UserRequest",
        "protocol": "rest",
        "method": "POST",
        "custom_data": "{bad json}"
    }
    rv = client.post('/test_api', json=payload)
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data