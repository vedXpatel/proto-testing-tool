package com.proto.testing.demo.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ApiTestRequest {
    @JsonProperty("api_url")
    private String apiUrl;
    
    @JsonProperty("proto_file")
    private String protoFile;
    
    @JsonProperty("message_type")
    private String messageType;
    
    @JsonProperty("method")
    private String method = "POST";
    
    @JsonProperty("json_payload")
    private String jsonPayload;
    
    @JsonProperty("headers")
    private java.util.Map<String, String> headers = new java.util.HashMap<>();
    
    // Constructors
    public ApiTestRequest() {}
    
    // Getters and setters
    public String getApiUrl() { return apiUrl; }
    public void setApiUrl(String apiUrl) { this.apiUrl = apiUrl; }
    
    public String getProtoFile() { return protoFile; }
    public void setProtoFile(String protoFile) { this.protoFile = protoFile; }
    
    public String getMessageType() { return messageType; }
    public void setMessageType(String messageType) { this.messageType = messageType; }
    
    public String getMethod() { return method; }
    public void setMethod(String method) { this.method = method; }
    
    public String getJsonPayload() { return jsonPayload; }
    public void setJsonPayload(String jsonPayload) { this.jsonPayload = jsonPayload; }
    
    public java.util.Map<String, String> getHeaders() { return headers; }
    public void setHeaders(java.util.Map<String, String> headers) { this.headers = headers; }
}