package com.example.calculatorservice.calculator;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class CalculatorControllerIT {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void shouldAddTwoNumbersOverHttp() {
        // when
        ResponseEntity<CalculationResponse> response =
                restTemplate.getForEntity("/api/v1/calculator/add?a=2&b=3", CalculationResponse.class);

        // then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().result()).isEqualTo(5.0);
    }

    @Test
    void shouldReturn400ForUnknownOperationOverHttp() {
        // when
        ResponseEntity<String> response =
                restTemplate.getForEntity("/api/v1/calculator/modulo?a=1&b=2", String.class);

        // then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }
}
