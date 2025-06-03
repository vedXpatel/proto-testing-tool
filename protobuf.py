from flask import Flask, request, jsonify, render_template_string
import os
import subprocess
import importlib.util
import sys
import json
import requests
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson, Parse
from google.protobuf.descriptor import FieldDescriptor
import tempfile
import shutil
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROTO_FOLDER'] = 'proto_compiled'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROTO_FOLDER'], exist_ok=True)

# Sample Proto Definition
SAMPLE_PROTO_CONTENT = """
syntax = "proto3";

message UserRequest {
    string name = 1;
    int32 age = 2;
    string email = 3;
    bool active = 4;
    repeated string tags = 5;
}

message UserResponse {
    string id = 1;
    string status = 2;
    string message = 3;
    UserRequest user = 4;
    int64 timestamp = 5;
}

message ProductRequest {
    string product_name = 1;
    double price = 2;
    int32 quantity = 3;
    string category = 4;
}

message ProductResponse {
    string product_id = 1;
    string status = 2;
    ProductRequest product = 3;
    double total_value = 4;
}
"""

# In-memory sample data store
sample_users = {}
sample_products = {}
next_user_id = 1
next_product_id = 1

class ProtobufService:
    def __init__(self):
        self.compiled_modules = {}
    
    def compile_proto(self, proto_file_path):
        """Compile .proto file to Python modules"""
        try:
            proto_dir = os.path.dirname(proto_file_path)
            output_dir = app.config['PROTO_FOLDER']
            
            # Use protoc to compile
            cmd = [
                'protoc',
                f'--python_out={output_dir}',
                f'--proto_path={proto_dir}',
                proto_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, f"Protoc compilation failed: {result.stderr}"
            
            return True, "Proto file compiled successfully"
            
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    def load_proto_module(self, proto_filename):
        """Load compiled protobuf module"""
        try:
            # Convert filename to module name
            module_name = proto_filename.replace('.proto', '_pb2.py')
            module_path = os.path.join(app.config['PROTO_FOLDER'], module_name)
            
            if not os.path.exists(module_path):
                return None, f"Compiled module not found: {module_path}"
            
            # Load module dynamically
            spec = importlib.util.spec_from_file_location("proto_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module, None
            
        except Exception as e:
            return None, f"Module loading error: {str(e)}"
    
    def generate_test_data(self, message_class):
        """Generate test data for protobuf message"""
        try:
            message = message_class()
            
            # Fill fields with sample data based on type
            for field in message.DESCRIPTOR.fields:
                if field.label == FieldDescriptor.LABEL_REPEATED:
                    if field.type == FieldDescriptor.TYPE_STRING:
                        getattr(message, field.name).extend([f"tag1_{field.name}", f"tag2_{field.name}"])
                    continue
                
                if field.type == FieldDescriptor.TYPE_STRING:
                    setattr(message, field.name, f"test_{field.name}")
                elif field.type == FieldDescriptor.TYPE_INT32:
                    setattr(message, field.name, 123)
                elif field.type == FieldDescriptor.TYPE_INT64:
                    setattr(message, field.name, int(time.time()))
                elif field.type == FieldDescriptor.TYPE_BOOL:
                    setattr(message, field.name, True)
                elif field.type == FieldDescriptor.TYPE_DOUBLE:
                    setattr(message, field.name, 3.14)
                elif field.type == FieldDescriptor.TYPE_FLOAT:
                    setattr(message, field.name, 2.71)
            
            return message, None
            
        except Exception as e:
            return None, f"Test data generation error: {str(e)}"

protobuf_service = ProtobufService()

def create_sample_proto():
    """Create sample proto file on startup"""
    sample_proto_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample.proto')
    with open(sample_proto_path, 'w') as f:
        f.write(SAMPLE_PROTO_CONTENT)
    
    # Compile it
    success, message = protobuf_service.compile_proto(sample_proto_path)
    if success:
        print("✅ Sample proto file created and compiled successfully")
    else:
        print(f"❌ Failed to compile sample proto: {message}")

# Sample API Endpoints (these simulate real APIs that accept protobuf)

@app.route('/api/users', methods=['POST'])
def create_user():
    """Sample API endpoint that accepts both JSON and Protobuf"""
    global next_user_id
    
    try:
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/x-protobuf' in content_type:
            # Handle protobuf request
            try:
                # Load the sample proto module
                module, error = protobuf_service.load_proto_module('sample.proto')
                if not module:
                    return jsonify({'error': 'Proto module not available'}), 500
                
                # Parse protobuf data
                user_request = module.UserRequest()
                user_request.ParseFromString(request.data)
                
                # Create response
                user_response = module.UserResponse()
                user_response.id = f"user_{next_user_id}"
                user_response.status = "created"
                user_response.message = "User created successfully via protobuf"
                user_response.user.CopyFrom(user_request)
                user_response.timestamp = int(time.time())
                
                # Store user
                sample_users[user_response.id] = {
                    'name': user_request.name,
                    'age': user_request.age,
                    'email': user_request.email,
                    'active': user_request.active,
                    'tags': list(user_request.tags)
                }
                next_user_id += 1
                
                # Return protobuf response
                response = app.response_class(
                    response=user_response.SerializeToString(),
                    status=201,
                    headers={'Content-Type': 'application/x-protobuf'}
                )
                return response
                
            except Exception as e:
                return jsonify({'error': f'Protobuf parsing error: {str(e)}'}), 400
        
        else:
            # Handle JSON request
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            user_id = f"user_{next_user_id}"
            sample_users[user_id] = data
            next_user_id += 1
            
            response = {
                'id': user_id,
                'status': 'created',
                'message': 'User created successfully via JSON',
                'user': data,
                'timestamp': int(time.time())
            }
            
            return jsonify(response), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    """Sample API endpoint for products"""
    global next_product_id
    
    try:
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/x-protobuf' in content_type:
            # Handle protobuf request
            try:
                module, error = protobuf_service.load_proto_module('sample.proto')
                if not module:
                    return jsonify({'error': 'Proto module not available'}), 500
                
                product_request = module.ProductRequest()
                product_request.ParseFromString(request.data)
                
                product_response = module.ProductResponse()
                product_response.product_id = f"prod_{next_product_id}"
                product_response.status = "created"
                product_response.product.CopyFrom(product_request)
                product_response.total_value = product_request.price * product_request.quantity
                
                # Store product
                sample_products[product_response.product_id] = {
                    'product_name': product_request.product_name,
                    'price': product_request.price,
                    'quantity': product_request.quantity,
                    'category': product_request.category
                }
                next_product_id += 1
                
                response = app.response_class(
                    response=product_response.SerializeToString(),
                    status=201,
                    headers={'Content-Type': 'application/x-protobuf'}
                )
                return response
                
            except Exception as e:
                return jsonify({'error': f'Protobuf parsing error: {str(e)}'}), 400
        
        else:
            # Handle JSON request
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            product_id = f"prod_{next_product_id}"
            sample_products[product_id] = data
            next_product_id += 1
            
            response = {
                'product_id': product_id,
                'status': 'created',
                'product': data,
                'total_value': data.get('price', 0) * data.get('quantity', 0)
            }
            
            return jsonify(response), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    return jsonify({'users': sample_users})

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    return jsonify({'products': sample_products})

@app.route('/')
def index():
    """Main interface with sample API testing"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protobuf API Testing Service with Sample APIs</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1000px; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .sample-section { background: #f0f8ff; }
            textarea { width: 100%; height: 120px; }
            input, button, select { margin: 5px; padding: 10px; }
            .result { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f2f2f2; }
            .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Protobuf API Testing Service</h1>
            <p><strong>Sample APIs running on this server:</strong></p>
            <ul>
                <li><code>POST /api/users</code> - Create users (JSON or Protobuf)</li>
                <li><code>POST /api/products</code> - Create products (JSON or Protobuf)</li>
                <li><code>GET /api/users</code> - List all users</li>
                <li><code>GET /api/products</code> - List all products</li>
            </ul>
            
            <div class="section sample-section">
                <h2>📋 Sample Proto Schema</h2>
                <div class="code">{{ proto_content }}</div>
                <p><em>This proto file is automatically created and compiled when the service starts.</em></p>
            </div>
            
            <div class="section">
                <h2>1. Upload Custom Proto File (Optional)</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" name="proto_file" accept=".proto">
                    <button type="submit">Upload & Compile</button>
                </form>
                <div id="uploadResult" class="result"></div>
            </div>
            
            <div class="section">
                <h2>2. Test Sample APIs</h2>
                <form id="testForm">
                    <table>
                        <tr>
                            <td><strong>API URL:</strong></td>
                            <td>
                                <select name="api_url" style="width: 300px;">
                                    <option value="http://localhost:8080/api/users">POST /api/users</option>
                                    <option value="http://localhost:8080/api/products">POST /api/products</option>
                                    <option value="http://localhost:8080/api/users">GET /api/users</option>
                                    <option value="http://localhost:8080/api/products">GET /api/products</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Message Type:</strong></td>
                            <td>
                                <select name="message_type">
                                    <option value="UserRequest">UserRequest</option>
                                    <option value="ProductRequest">ProductRequest</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Protocol:</strong></td>
                            <td>
                                <select name="protocol">
                                    <option value="rest">REST (JSON)</option>
                                    <option value="protobuf">Protobuf Binary</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Method:</strong></td>
                            <td>
                                <select name="method">
                                    <option value="POST">POST</option>
                                    <option value="GET">GET</option>
                                </select>
                            </td>
                        </tr>
                    </table>
                    
                    <p><strong>Custom Test Data (JSON, leave empty for auto-generation):</strong></p>
                    <textarea name="custom_data" placeholder='Example: {"name": "John Doe", "age": 30, "email": "john@example.com", "active": true, "tags": ["developer", "python"]}'></textarea>
                    
                    <br><button type="submit">🚀 Test API</button>
                    <button type="button" onclick="generateSampleData()">📝 Generate Sample Data</button>
                </form>
                <div id="testResult" class="result"></div>
            </div>
            
            <div class="section">
                <h2>3. View Current Data</h2>
                <button onclick="loadUsers()">👥 Load Users</button>
                <button onclick="loadProducts()">📦 Load Products</button>
                <div id="dataResult" class="result"></div>
            </div>
        </div>
        
        <script>
            const protoContent = `{{ proto_content }}`;
            
            function generateSampleData() {
                const messageType = document.querySelector('select[name="message_type"]').value;
                let sampleData;
                
                if (messageType === 'UserRequest') {
                    sampleData = {
                        "name": "John Doe",
                        "age": 30,
                        "email": "john.doe@example.com",
                        "active": true,
                        "tags": ["developer", "python", "protobuf"]
                    };
                } else if (messageType === 'ProductRequest') {
                    sampleData = {
                        "product_name": "Awesome Widget",
                        "price": 29.99,
                        "quantity": 5,
                        "category": "Electronics"
                    };
                }
                
                document.querySelector('textarea[name="custom_data"]').value = JSON.stringify(sampleData, null, 2);
            }
            
            document.getElementById('uploadForm').onsubmit = async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                try {
                    const result = await fetch('/upload_proto', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await result.json();
                    const resultDiv = document.getElementById('uploadResult');
                    resultDiv.className = data.success ? 'result success' : 'result error';
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('uploadResult').innerHTML = 
                        '<div class="error">Error: ' + error.message + '</div>';
                }
            };
            
            document.getElementById('testForm').onsubmit = async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                try {
                    const result = await fetch('/test_api', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    const responseData = await result.json();
                    const resultDiv = document.getElementById('testResult');
                    resultDiv.className = responseData.success ? 'result success' : 'result error';
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(responseData, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('testResult').innerHTML = 
                        '<div class="error">Error: ' + error.message + '</div>';
                }
            };
            
            async function loadUsers() {
                try {
                    const result = await fetch('/api/users');
                    const data = await result.json();
                    document.getElementById('dataResult').innerHTML = 
                        '<h3>👥 Current Users:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('dataResult').innerHTML = 
                        '<div class="error">Error loading users: ' + error.message + '</div>';
                }
            }
            
            async function loadProducts() {
                try {
                    const result = await fetch('/api/products');
                    const data = await result.json();
                    document.getElementById('dataResult').innerHTML = 
                        '<h3>📦 Current Products:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('dataResult').innerHTML = 
                        '<div class="error">Error loading products: ' + error.message + '</div>';
                }
            }
        </script>
    </body>
    </html>
    ''', proto_content=SAMPLE_PROTO_CONTENT.strip())

@app.route('/upload_proto', methods=['POST'])
def upload_proto():
    """Handle proto file upload and compilation"""
    try:
        if 'proto_file' not in request.files:
            return jsonify({'error': 'No proto file provided'}), 400
        
        file = request.files['proto_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.proto'):
            return jsonify({'error': 'File must be a .proto file'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Compile proto file
        success, message = protobuf_service.compile_proto(filepath)
        
        if success:
            # Try to load and analyze the compiled module
            module, error = protobuf_service.load_proto_module(filename)
            if module:
                # Get available message types
                message_types = [
                    name for name in dir(module) 
                    if hasattr(getattr(module, name), 'DESCRIPTOR')
                ]
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'filename': filename,
                    'available_message_types': message_types
                })
            else:
                return jsonify({
                    'success': True,
                    'message': message,
                    'filename': filename,
                    'warning': f'Could not analyze module: {error}'
                })
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_api', methods=['POST'])
def test_api():
    """Test API endpoint with protobuf or REST"""
    try:
        data = request.json
        api_url = data.get('api_url')
        message_type = data.get('message_type')
        protocol = data.get('protocol', 'rest')
        method = data.get('method', 'POST')
        custom_data = data.get('custom_data', '')
        
        if not api_url or not message_type:
            return jsonify({'error': 'API URL and message type are required'}), 400
        
        # For GET requests, we don't need message data
        if method == 'GET':
            headers = {'Content-Type': 'application/json'}
            response = requests.get(api_url, headers=headers, timeout=30)
            
            response_data = None
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
            else:
                response_data = response.text
            
            return jsonify({
                'success': True,
                'request': {
                    'url': api_url,
                    'method': method,
                    'headers': dict(headers)
                },
                'response': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'data': response_data,
                    'success': 200 <= response.status_code < 300
                }
            })
        
        # Find the proto module that contains this message type
        proto_module = None
        message_class = None
        
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.proto'):
                module, error = protobuf_service.load_proto_module(filename)
                if module and hasattr(module, message_type):
                    proto_module = module
                    message_class = getattr(module, message_type)
                    break
        
        if not message_class:
            return jsonify({'error': f'Message type {message_type} not found'}), 400
        
        # Generate or parse test data
        if custom_data.strip():
            try:
                test_data_dict = json.loads(custom_data)
                test_message = message_class()
                Parse(json.dumps(test_data_dict), test_message)
            except Exception as e:
                return jsonify({'error': f'Invalid custom data: {str(e)}'}), 400
        else:
            test_message, error = protobuf_service.generate_test_data(message_class)
            if error:
                return jsonify({'error': error}), 400
        
        # Prepare request based on protocol
        headers = {}
        payload = None
        
        if protocol == 'protobuf':
            headers['Content-Type'] = 'application/x-protobuf'
            payload = test_message.SerializeToString()
        else:  # REST/JSON
            headers['Content-Type'] = 'application/json'
            payload = MessageToJson(test_message)
        
        # Make API request
        if method == 'POST':
            response = requests.post(api_url, headers=headers, data=payload, timeout=30)
        elif method == 'PUT':
            response = requests.put(api_url, headers=headers, data=payload, timeout=30)
        else:
            return jsonify({'error': 'Unsupported HTTP method for this request type'}), 400
        
        # Parse response
        response_data = None
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_data = response.json()
            except:
                response_data = response.text
        elif 'application/x-protobuf' in response.headers.get('content-type', ''):
            response_data = f"<Binary protobuf data: {len(response.content)} bytes>"
        else:
            response_data = response.text
        
        result = {
            'success': True,
            'request': {
                'url': api_url,
                'method': method,
                'protocol': protocol,
                'headers': dict(headers),
                # 'payload': payload.decode('utf-8') if protocol == 'rest' else f'<binary data: {len(payload)} bytes>',
                'test_data_used': MessageToJson(test_message)
            },
            'response': {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data,
                'success': 200 <= response.status_code < 300
            }
        }
        
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'API request failed: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask Protobuf API Testing Service with Sample APIs...")
    print("📋 Required system dependencies:")
    print("   - protoc compiler: brew install protobuf (macOS) or apt-get install protobuf-compiler (Ubuntu)")
    print("📦 Required Python packages: flask, protobuf, requests, werkzeug")
    print()
    
    # Create sample proto file
    create_sample_proto()
    
    PORT = 8080
    print(f"🌐 Service available at: http://localhost:{PORT}")
    print("🧪 Sample APIs:")
    print(f"   - POST http://localhost:{PORT}/api/users")
    print(f"   - POST http://localhost:{PORT}/api/products") 
    print(f"   - GET  http://localhost:{PORT}/api/users")
    print(f"   - GET  http://localhost:{PORT}/api/products")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=PORT)