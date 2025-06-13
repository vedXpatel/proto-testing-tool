package com.proto.testing.demo.service;

import com.proto.testing.demo.model.ApiTestRequest;
import com.proto.testing.demo.model.ApiTestResponse;
import com.google.protobuf.Message;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.methods.HttpPut;
import org.apache.hc.client5.http.classic.methods.HttpUriRequestBase;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.ByteArrayEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@Service
public class ApiConsumerService {
    
    @Autowired
    private ProtobufService protobufService;
    
    public ApiTestResponse consumeProtobufApi(ApiTestRequest request) {
        ApiTestResponse response = new ApiTestResponse();
        long startTime = System.currentTimeMillis();
        
        try {
            // Convert JSON to Protobuf
            Message protobufMessage = protobufService.convertJsonToProtobuf(
                request.getJsonPayload(), 
                request.getMessageType()
            );
            
            byte[] protobufBytes = protobufMessage.toByteArray();
            
            // Prepare HTTP request
            HttpUriRequestBase httpRequest = createHttpRequest(request.getMethod(), request.getApiUrl());
            
            // Set headers
            httpRequest.setHeader("Content-Type", "application/x-protobuf");
            if (request.getHeaders() != null) {
                for (Map.Entry<String, String> header : request.getHeaders().entrySet()) {
                    httpRequest.setHeader(header.getKey(), header.getValue());
                }
            }
            
            // Set protobuf payload for POST/PUT requests
            if (httpRequest instanceof HttpPost) {
                ((HttpPost) httpRequest).setEntity(new ByteArrayEntity(protobufBytes, ContentType.create("application/x-protobuf")));
            } else if (httpRequest instanceof HttpPut) {
                ((HttpPut) httpRequest).setEntity(new ByteArrayEntity(protobufBytes, ContentType.create("application/x-protobuf")));
            }
            
            // Execute request
            try (CloseableHttpClient client = HttpClients.createDefault();
                 CloseableHttpResponse httpResponse = client.execute(httpRequest)) {
                
                long endTime = System.currentTimeMillis();
                
                // Build response
                response.setSuccess(true);
                
                // Request info
                ApiTestResponse.RequestInfo requestInfo = new ApiTestResponse.RequestInfo();
                requestInfo.setUrl(request.getApiUrl());
                requestInfo.setMethod(request.getMethod());
                requestInfo.setHeaders(request.getHeaders());
                requestInfo.setJsonPayload(request.getJsonPayload());
                requestInfo.setProtobufSize(protobufBytes.length);
                response.setRequest(requestInfo);
                
                // Response info
                ApiTestResponse.ResponseInfo responseInfo = new ApiTestResponse.ResponseInfo();
                responseInfo.setStatusCode(httpResponse.getCode());
                responseInfo.setResponseTimeMs(endTime - startTime);
                responseInfo.setSuccess(httpResponse.getCode() >= 200 && httpResponse.getCode() < 300);
                
                // Response headers
                Map<String, String> responseHeaders = new HashMap<>();
                for (var header : httpResponse.getHeaders()) {
                    responseHeaders.put(header.getName(), header.getValue());
                }
                responseInfo.setHeaders(responseHeaders);
                
                // Response body
                if (httpResponse.getEntity() != null) {
                    String responseBody = EntityUtils.toString(httpResponse.getEntity());
                    responseInfo.setData(responseBody);
                }
                
                response.setResponse(responseInfo);
                
            }
            
        } catch (Exception e) {
            response.setSuccess(false);
            response.setError("API call failed: " + e.getMessage());
        }
        
        return response;
    }
    
    private HttpUriRequestBase createHttpRequest(String method, String url) {
        switch (method.toUpperCase()) {
            case "GET":
                return new HttpGet(url);
            case "POST":
                return new HttpPost(url);
            case "PUT":
                return new HttpPut(url);
            default:
                throw new IllegalArgumentException("Unsupported HTTP method: " + method);
        }
    }
}