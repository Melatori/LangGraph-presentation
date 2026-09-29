package com.example.hello;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
class HelloController {

    @GetMapping("/api/v1/hello")
    HelloResponse hello() {
        return new HelloResponse("Hello, World!");
    }
}
