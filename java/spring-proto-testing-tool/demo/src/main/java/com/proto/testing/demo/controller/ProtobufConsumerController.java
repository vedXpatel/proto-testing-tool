package com.proto.testing.demo.controller;

import com.proto.testing.demo.model.ApiTestRequest;
import com.proto.testing.demo.model.ApiTestResponse;
import com.proto.testing.demo.service.ApiConsumerService;
import com.proto.testing.demo.service.ProtobufService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@Controller
public class ProtobufConsumerController {
    
    @Autowired
    private ProtobufService protobufService;
    
    @Autowired
    private ApiConsumerService apiConsumerService;
    
    @GetMapping("/")
    public String index(Model model) {
        model.addAttribute("availableTypes", protobufService.getAvailableMessageTypes());
        return "index";
    }
    
    @PostMapping("/upload-proto")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> uploadProto(@RequestParam("proto_file") MultipartFile file) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            String filename = protobufService.uploadAndCompileProto(file);
            response.put("success", true);
            response.put("message", "Proto file compiled successfully");
            response.put("filename", filename);
            response.put("available_types", protobufService.getAvailableMessageTypes());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
    
    @PostMapping("/test-api")
    @ResponseBody
    public ResponseEntity<ApiTestResponse> testApi(@RequestBody ApiTestRequest request) {
        try {
            ApiTestResponse response = apiConsumerService.consumeProtobufApi(request);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            ApiTestResponse errorResponse = new ApiTestResponse();
            errorResponse.setSuccess(false);
            errorResponse.setError("Request processing failed: " + e.getMessage());
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }
    
    @GetMapping("/api/message-types")
    @ResponseBody
    public ResponseEntity<Set<String>> getMessageTypes() {
        return ResponseEntity.ok(protobufService.getAvailableMessageTypes());
    }
    
    @GetMapping("/api/sample-json/{messageType}")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> getSampleJson(@PathVariable String messageType) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            String sampleJson = protobufService.generateSampleJson(messageType);
            response.put("success", true);
            response.put("message_type", messageType);
            response.put("sample_json", sampleJson);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
}