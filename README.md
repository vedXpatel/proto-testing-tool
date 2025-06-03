# proto-testing-tool

A Flask-based web service for testing Protobuf and REST APIs with live endpoints and dynamic proto file compilation.

## Features

- **Sample REST & Protobuf APIs:**  
  - `POST /api/users` — Create users (accepts JSON or Protobuf)
  - `POST /api/products` — Create products (accepts JSON or Protobuf)
  - `GET /api/users` — List all users
  - `GET /api/products` — List all products

- **Proto File Upload & Compilation:**  
  Upload your own `.proto` files and the service will compile and make them available for testing.

- **API Testing Interface:**  
  Web UI to test APIs using either JSON (REST) or Protobuf binary, with auto-generated or custom test data.

- **Automated Test Suite:**  
  Includes `pytest`-based tests for all endpoints and features.

## Requirements

- **System:**  
  - Python 3.8+
  - `protoc` compiler  
    - macOS: `brew install protobuf`
    - Ubuntu: `sudo apt-get install protobuf-compiler`

- **Python Packages:**

## Usage

1. **Start the Service:**

The service will be available at [http://localhost:8080](http://localhost:8080).

2. **Web Interface:**  
Open [http://localhost:8080](http://localhost:8080) in your browser to:
- View the sample proto schema
- Upload custom proto files
- Test sample APIs with JSON or Protobuf
- View current users and products

3. **API Endpoints:**

| Endpoint                | Method | Content-Type           | Description                |
|-------------------------|--------|------------------------|----------------------------|
| `/api/users`            | POST   | JSON / x-protobuf      | Create a user              |
| `/api/products`         | POST   | JSON / x-protobuf      | Create a product           |
| `/api/users`            | GET    |                        | List all users             |
| `/api/products`         | GET    |                        | List all products          |
| `/upload_proto`         | POST   | multipart/form-data    | Upload and compile proto   |
| `/test_api`             | POST   | JSON                   | Test any API endpoint      |

## Running Tests

1. **Run all tests:**
2. **Check code coverage:**
3. **Generate HTML coverage report:**

## Notes

- The service auto-creates and compiles a sample proto file on startup.
- Uploaded proto files are compiled and available for use in the API tester.
- Protobuf endpoints require the `protoc` compiler to be installed on your system.

## License

MIT License
