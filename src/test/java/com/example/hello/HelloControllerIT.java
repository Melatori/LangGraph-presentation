package com.example.hello;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Integration test: starts the full application context on a random port
 * and calls it over real HTTP.
 */
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class HelloControllerIT {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void shouldReturnHelloWorldMessageOverHttp() {
        ResponseEntity<HelloResponse> response =
                restTemplate.getForEntity("/api/v1/hello", HelloResponse.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getHeaders().getContentType()).isEqualTo(MediaType.APPLICATION_JSON);
        assertThat(response.getBody()).isEqualTo(new HelloResponse("Hello, World!"));
    }

    @Test
    void shouldReturnNotFoundForUnknownEndpoint() {
        ResponseEntity<String> response =
                restTemplate.getForEntity("/api/v1/unknown", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }
}
