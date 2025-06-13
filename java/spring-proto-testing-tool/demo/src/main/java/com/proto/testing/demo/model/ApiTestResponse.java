package com.proto.testing.demo.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public class ApiTestResponse {
    private boolean success;
    private String error;
    private RequestInfo request;
    private ResponseInfo response;
    
    public static class RequestInfo {
        private String url;
        private String method;
        private Map<String, String> headers;
        
        @JsonProperty("json_payload")
        private String jsonPayload;
        
        @JsonProperty("protobuf_size")
        private int protobufSize;
        
        // Getters and setters
        public String getUrl() { return url; }
        public void setUrl(String url) { this.url = url; }
        
        public String getMethod() { return method; }
        public void setMethod(String method) { this.method = method; }
        
        public Map<String, String> getHeaders() { return headers; }
        public void setHeaders(Map<String, String> headers) { this.headers = headers; }
        
        public String getJsonPayload() { return jsonPayload; }
        public void setJsonPayload(String jsonPayload) { this.jsonPayload = jsonPayload; }
        
        public int getProtobufSize() { return protobufSize; }
        public void setProtobufSize(int protobufSize) { this.protobufSize = protobufSize; }
    }
    
    public static class ResponseInfo {
        @JsonProperty("status_code")
        private int statusCode;
        private Map<String, String> headers;
        private Object data;
        private boolean success;
        
        @JsonProperty("response_time_ms")
        private long responseTimeMs;
        
        // Getters and setters
        public int getStatusCode() { return statusCode; }
        public void setStatusCode(int statusCode) { this.statusCode = statusCode; }
        
        public Map<String, String> getHeaders() { return headers; }
        public void setHeaders(Map<String, String> headers) { this.headers = headers; }
        
        public Object getData() { return data; }
        public void setData(Object data) { this.data = data; }
        
        public boolean isSuccess() { return success; }
        public void setSuccess(boolean success) { this.success = success; }
        
        public long getResponseTimeMs() { return responseTimeMs; }
        public void setResponseTimeMs(long responseTimeMs) { this.responseTimeMs = responseTimeMs; }
    }
    
    // Getters and setters
    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }
    
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
    
    public RequestInfo getRequest() { return request; }
    public void setRequest(RequestInfo request) { this.request = request; }
    
    public ResponseInfo getResponse() { return response; }
    public void setResponse(ResponseInfo response) { this.response = response; }
}