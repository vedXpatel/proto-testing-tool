# Spring Boot Protobuf API Consumer

A Spring Boot application that allows you to upload protobuf (.proto) files, provide JSON input, and test APIs that consume protobuf messages. The application automatically converts JSON payloads to protobuf format before sending requests.

## Features

- **Proto File Upload & Compilation**: Upload .proto files and automatically compile them to Java classes
- **JSON to Protobuf Conversion**: Input data as JSON and automatically convert to protobuf binary format
- **API Testing**: Test protobuf-consuming APIs with various HTTP methods (GET, POST, PUT)
- **Sample Data Generation**: Generate sample JSON data based on protobuf message definitions
- **Web Interface**: User-friendly web interface for all operations
- **Real-time Results**: View request/response details, timing, and status codes

## Prerequisites

1. **Java 17+**
2. **Maven 3.6+**
3. **Protocol Buffers Compiler (protoc)**

### Installing protoc

**macOS:**
```bash
brew install protobuf
```

**Ubuntu/Debian:**
```bash
sudo apt-get install protobuf-compiler
```

**Windows:**
Download from [Protocol Buffers releases](https://github.com/protocolbuffers/protobuf/releases) and add to PATH.

## Quick Start

1. **Clone and build the project:**
```bash
git clone <repository-url>
cd protobuf-consumer
mvn clean install
```

2. **Run the application:**
```bash
mvn spring-boot:run
```

3. **Open your browser:**
Navigate to `http://localhost:8080`

## Usage

### 1. Upload Protobuf File

1. Click "Choose File" and select your `.proto` file
2. Click "Upload & Compile" 
3. The application will compile the proto file and show available message types

### 2. Test API Endpoint

1. Enter the API URL that accepts protobuf messages
2. Select the message type from the dropdown
3. Choose HTTP method (POST, PUT, or GET)
4. Add custom headers if needed (JSON format)
5. Enter JSON payload or click "Generate Sample JSON"
6. Click "Send Protobuf Request"

### 3. View Results

The application shows:
- Request details (URL, method, headers, JSON payload, protobuf size)
- Response details (status code, headers, response time, body)
- Success/error status

## Example Proto File

```protobuf
syntax = "proto3";

package example;

message UserRequest {
    string name = 1;
    int32 age = 2;
    string email = 3;
    repeated string interests = 4;
}

message UserResponse {
    string id = 1;
    string message = 2;
    bool success = 3;
}
```

## Example JSON Input

```json
{
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com",
    "interests": ["programming", "music"]
}
```

## API Endpoints

- `GET /` - Main web interface
- `POST /upload-proto` - Upload and compile proto files
- `POST /test-api` - Test protobuf API endpoints
- `GET /api/message-types` - Get available message types
- `GET /api/sample-json/{messageType}` - Generate sample JSON for message type

## Configuration

Edit `src/main/resources/application.yml`:

```yaml
server:
  port: 8080  # Change port if needed

spring:
  servlet:
    multipart:
      max-file-size: 16MB  # Adjust file size limit
      max-request-size: 16MB
```

## Troubleshooting

### Common Issues

1. **"protoc command not found"**
   - Install Protocol Buffers compiler (see Prerequisites)
   - Ensure `protoc` is in your system PATH

2. **"Java compiler not available"**
   - Ensure you're running on JDK (not JRE)
   - Set JAVA_HOME to JDK installation

3. **"Message type not found"**
   - Ensure proto file was uploaded and compiled successfully
   - Check that message type name matches exactly

### Debugging

Enable debug logging by adding to `application.yml`:
```yaml
logging:
  level:
    com.proto.testing.demo: DEBUG
```

## Docker Support

Create a `Dockerfile`:

```dockerfile
FROM openjdk:17-jdk-slim

# Install protoc
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*

COPY target/protobuf-consumer-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

Build and run:
```bash
mvn clean package
docker build -t protobuf-consumer .
docker run -p 8080:8080 protobuf-consumer
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.