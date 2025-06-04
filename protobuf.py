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

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROTO_FOLDER'] = 'proto_compiled'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROTO_FOLDER'], exist_ok=True)

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
                    continue  # Skip repeated fields for simplicity
                
                if field.type == FieldDescriptor.TYPE_STRING:
                    setattr(message, field.name, f"test_{field.name}")
                elif field.type == FieldDescriptor.TYPE_INT32:
                    setattr(message, field.name, 123)
                elif field.type == FieldDescriptor.TYPE_INT64:
                    setattr(message, field.name, 456)
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

@app.route('/')
def index():
    """Main interface"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protobuf API Testing Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
            textarea { width: 100%; height: 150px; }
            input, button { margin: 5px; padding: 10px; }
            .result { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Protobuf API Testing Service</h1>
            
            <div class="section">
                <h2>1. Upload Proto File</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" name="proto_file" accept=".proto" required>
                    <button type="submit">Upload & Compile</button>
                </form>
                <div id="uploadResult" class="result"></div>
            </div>
            
            <div class="section">
                <h2>2. Test API Endpoint</h2>
                <form id="testForm">
                    <input type="text" name="api_url" placeholder="API URL" required style="width: 100%;">
                    <input type="text" name="message_type" placeholder="Message Type (e.g., UserRequest)" required>
                    <select name="protocol">
                        <option value="rest">REST (JSON)</option>
                        <option value="protobuf">Protobuf Binary</option>
                    </select>
                    <select name="method">
                        <option value="POST">POST</option>
                        <option value="GET">GET</option>
                        <option value="PUT">PUT</option>
                    </select>
                    <br>
                    <textarea name="custom_data" placeholder="Custom test data (JSON format, leave empty to auto-generate)"></textarea>
                    <br>
                    <button type="submit">Test API</button>
                </form>
                <div id="testResult" class="result"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('uploadForm').onsubmit = async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const result = await fetch('/upload_proto', {
                    method: 'POST',
                    body: formData
                });
                const data = await result.json();
                document.getElementById('uploadResult').innerHTML = 
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            };
            
            document.getElementById('testForm').onsubmit = async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                const result = await fetch('/test_api', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const responseData = await result.json();
                document.getElementById('testResult').innerHTML = 
                    '<pre>' + JSON.stringify(responseData, null, 2) + '</pre>';
            };
        </script>
    </body>
    </html>
    ''')

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
        start_time = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC').json()['unixtime'] if True else 0
        
        if method == 'GET':
            response = requests.get(api_url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(api_url, headers=headers, data=payload, timeout=30)
        elif method == 'PUT':
            response = requests.put(api_url, headers=headers, data=payload, timeout=30)
        else:
            return jsonify({'error': 'Unsupported HTTP method'}), 400
        
        # Parse response
        response_data = None
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_data = response.json()
            except:
                response_data = response.text
        else:
            response_data = response.text
        
        result = {
            'success': True,
            'request': {
                'url': api_url,
                'method': method,
                'protocol': protocol,
                'headers': dict(headers),
                'payload': payload.decode('utf-8') if protocol == 'rest' else f'<binary data: {len(payload)} bytes>',
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

@app.route('/generate_test_data/<message_type>')
def generate_test_data_endpoint(message_type):
    """Generate test data for a specific message type"""
    try:
        # Find the message class
        message_class = None
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.proto'):
                module, error = protobuf_service.load_proto_module(filename)
                if module and hasattr(module, message_type):
                    message_class = getattr(module, message_type)
                    break
        
        if not message_class:
            return jsonify({'error': f'Message type {message_type} not found'}), 404
        
        test_message, error = protobuf_service.generate_test_data(message_class)
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'message_type': message_type,
            'test_data': json.loads(MessageToJson(test_message))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list_message_types')
def list_message_types():
    """List all available message types from uploaded proto files"""
    try:
        all_types = {}
        
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.proto'):
                module, error = protobuf_service.load_proto_module(filename)
                if module:
                    message_types = [
                        name for name in dir(module) 
                        if hasattr(getattr(module, name), 'DESCRIPTOR')
                    ]
                    all_types[filename] = message_types
        
        return jsonify({'message_types': all_types})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Protobuf API Testing Service...")
    print("Make sure you have protoc installed: brew install protobuf (macOS) or apt-get install protobuf-compiler (Ubuntu)")
    print("Required Python packages: flask, protobuf, requests")
    
    # You can change the port here
    PORT = 8080  # Change this to any available port (e.g., 3000, 8000, 8080, 9000)
    
    print(f"Service will be available at: http://localhost:{PORT}")
    app.run(debug=True, host='0.0.0.0', port=PORT)