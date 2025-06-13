package com.proto.testing.demo.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.proto.testing.demo.service.SampleProtobufApiService;

@RestController
@RequestMapping("/api/sample")
public class SampleProtobufApiController {
    @Autowired
    private SampleProtobufApiService sampleService;

    @PostMapping("/echo/{messageType}")
    public ResponseEntity<?> echoProtobuf(@PathVariable String messageType, @RequestBody String jsonPayload) {
        return sampleService.echoProtobuf(messageType, jsonPayload);
    }

    @GetMapping("/sample-user-request")
    public ResponseEntity<?> getSampleUserRequest() {
        return sampleService.sampleUserRequest();
    }

    @GetMapping("/sample-user-response")
    public ResponseEntity<?> getSampleUserResponse() {
        return sampleService.sampleUserResponse();
    }

    @GetMapping("/sample-product-request")
    public ResponseEntity<?> getSampleProductRequest() {
        return sampleService.sampleProductRequest();
    }

    @GetMapping("/sample-product-response")
    public ResponseEntity<?> getSampleProductResponse() {
        return sampleService.sampleProductResponse();
    }
}
