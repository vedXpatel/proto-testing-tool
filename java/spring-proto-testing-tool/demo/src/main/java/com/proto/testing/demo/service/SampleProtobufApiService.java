package com.proto.testing.demo.service;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.HashMap;
import java.util.Map;

@Service
public class SampleProtobufApiService {

    /**
     * Returns a sample UserRequest JSON.
     */
    @GetMapping(value = "/sample-user-request", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> sampleUserRequest() {
        String json = "{\"name\":\"Alice\",\"age\":30,\"email\":\"alice@example.com\",\"active\":true,\"tags\":[\"admin\",\"user\"]}";
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("sample", json);
        return ResponseEntity.ok(response);
    }

    /**
     * Returns a sample UserResponse JSON.
     */
    @GetMapping(value = "/sample-user-response", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> sampleUserResponse() {
        String json = "{\"id\":\"123\",\"status\":\"OK\",\"message\":\"User created\",\"user\":{\"name\":\"Alice\",\"age\":30,\"email\":\"alice@example.com\",\"active\":true,\"tags\":[\"admin\"]},\"timestamp\":1686153600}";
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("sample", json);
        return ResponseEntity.ok(response);
    }

    /**
     * Returns a sample ProductRequest JSON.
     */
    @GetMapping(value = "/sample-product-request", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> sampleProductRequest() {
        String json = "{\"product_name\":\"Widget\",\"price\":19.99,\"quantity\":5,\"category\":\"gadgets\"}";
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("sample", json);
        return ResponseEntity.ok(response);
    }

    /**
     * Returns a sample ProductResponse JSON.
     */
    @GetMapping(value = "/sample-product-response", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> sampleProductResponse() {
        String json = "{\"product_id\":\"W123\",\"status\":\"IN_STOCK\",\"product\":{\"product_name\":\"Widget\",\"price\":19.99,\"quantity\":5,\"category\":\"gadgets\"},\"total_value\":99.95}";
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("sample", json);
        return ResponseEntity.ok(response);
    }
}