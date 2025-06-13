package com.proto.testing.demo.service;

import com.google.protobuf.Descriptors;
import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ProtobufService {
    
    private final Map<String, Class<?>> loadedMessageClasses = new ConcurrentHashMap<>();
    private final Path uploadDir = Paths.get("uploads");
    private final Path compiledDir = Paths.get("compiled");
    
    public ProtobufService() {
        try {
            Files.createDirectories(uploadDir);
            Files.createDirectories(compiledDir);
        } catch (IOException e) {
            throw new RuntimeException("Failed to create directories", e);
        }
    }
    
    public String uploadAndCompileProto(MultipartFile file) throws Exception {
        if (!file.getOriginalFilename().endsWith(".proto")) {
            throw new IllegalArgumentException("File must be a .proto file");
        }
        
        // Save uploaded file
        String filename = file.getOriginalFilename();
        Path protoPath = uploadDir.resolve(filename);
        Files.copy(file.getInputStream(), protoPath, 
                  java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        
        // Compile proto file
        compileProtoFile(protoPath);
        
        // Load compiled classes
        loadCompiledClasses(filename);
        
        return filename;
    }
    
    private void compileProtoFile(Path protoPath) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(
            "protoc",
            "--java_out=" + compiledDir.toAbsolutePath(),
            "--proto_path=" + uploadDir.toAbsolutePath(),
            protoPath.toAbsolutePath().toString()
        );
        
        Process process = pb.start();
        int exitCode = process.waitFor();
        
        if (exitCode != 0) {
            String errorOutput = new String(process.getErrorStream().readAllBytes());
            throw new RuntimeException("Proto compilation failed: " + errorOutput);
        }
    }
    
    private void loadCompiledClasses(String protoFilename) throws Exception {
        // Compile all .java files in the compiled directory
        File[] javaFiles = compiledDir.toFile().listFiles((dir, name) -> name.endsWith(".java"));
        if (javaFiles != null) {
            for (File javaFile : javaFiles) {
                compileJavaFile(javaFile);
            }
        }

        // Load all .class files using URLClassLoader
        File[] classFiles = compiledDir.toFile().listFiles((dir, name) -> name.endsWith(".class"));
        if (classFiles == null) return;

        URLClassLoader classLoader = new URLClassLoader(
            new URL[]{compiledDir.toUri().toURL()},
            this.getClass().getClassLoader()
        );

        for (File classFile : classFiles) {
            String className = classFile.getName().replace(".class", "");
            try {
                // For inner classes (e.g., Test$UserRequest), load them as well
                Class<?> clazz = classLoader.loadClass(className);
                if (com.google.protobuf.Message.class.isAssignableFrom(clazz)) {
                    loadedMessageClasses.put(clazz.getSimpleName(), clazz);
                }
            } catch (Throwable ignored) {
                // Ignore classes that can't be loaded
            }
        }
    }
    
    private void compileJavaFile(File javaFile) throws Exception {
        javax.tools.JavaCompiler compiler = javax.tools.ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new RuntimeException("Java compiler not available");
        }
        
        int result = compiler.run(null, null, null, javaFile.getAbsolutePath());
        if (result != 0) {
            throw new RuntimeException("Java compilation failed for: " + javaFile.getName());
        }
    }
    
    public Message convertJsonToProtobuf(String jsonPayload, String messageType) throws Exception {
        Class<?> messageClass = findMessageClass(messageType);
        if (messageClass == null) {
            throw new IllegalArgumentException("Message type not found: " + messageType);
        }
        
        // Get the default instance to create a builder
        Message.Builder builder = (Message.Builder) messageClass.getMethod("newBuilder").invoke(null);
        
        // Use JsonFormat to parse JSON into protobuf
        JsonFormat.parser().merge(jsonPayload, builder);
        
        return builder.build();
    }
    
    private Class<?> findMessageClass(String messageType) {
        // This is simplified - in practice, you'd maintain a proper registry
        // of loaded message classes from the compiled proto files
        for (Class<?> clazz : loadedMessageClasses.values()) {
            if (clazz.getSimpleName().equals(messageType)) {
                return clazz;
            }
        }
        return null;
    }
    
    public Set<String> getAvailableMessageTypes() {
        Set<String> types = new HashSet<>();
        for (Class<?> clazz : loadedMessageClasses.values()) {
            if (Message.class.isAssignableFrom(clazz)) {
                types.add(clazz.getSimpleName());
            }
        }
        return types;
    }
    
    public String generateSampleJson(String messageType) throws Exception {
        Class<?> messageClass = findMessageClass(messageType);
        if (messageClass == null) {
            throw new IllegalArgumentException("Message type not found: " + messageType);
        }
        
        // Create a default instance and convert to JSON
        Message defaultInstance = (Message) messageClass.getMethod("getDefaultInstance").invoke(null);
        return JsonFormat.printer().print(defaultInstance);
    }
}