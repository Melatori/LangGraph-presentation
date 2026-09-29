package com.example.hello;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.is;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Web layer slice test: starts only {@link HelloController} without the full application context.
 */
@WebMvcTest(HelloController.class)
class HelloControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void shouldReturnOkStatusWhenGetHello() throws Exception {
        mockMvc.perform(get("/api/v1/hello"))
                .andExpect(status().isOk());
    }

    @Test
    void shouldReturnJsonContentTypeWhenGetHello() throws Exception {
        mockMvc.perform(get("/api/v1/hello"))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void shouldReturnHelloWorldMessage() throws Exception {
        mockMvc.perform(get("/api/v1/hello"))
                .andExpect(jsonPath("$.message", is("Hello, World!")));
    }
}
