package com.example.calculatorservice.calculator;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

@WebMvcTest(CalculatorController.class)
class CalculatorControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private CalculatorService calculatorService;

    @Test
    void shouldReturnResultForValidOperation() throws Exception {
        // given
        given(calculatorService.calculate("add", 2.0, 3.0)).willReturn(new CalculationResponse(5.0));

        // when / then
        mockMvc.perform(get("/api/v1/calculator/add").param("a", "2").param("b", "3"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.result").value(5.0));
    }

    @Test
    void shouldReturn400WhenOperationIsUnknown() throws Exception {
        // given
        given(calculatorService.calculate(eq("modulo"), any(), any()))
                .willThrow(new InvalidCalculationException("Unknown operation: modulo"));

        // when / then
        mockMvc.perform(get("/api/v1/calculator/modulo").param("a", "1").param("b", "2"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void shouldReturn400WhenParameterIsMissing() throws Exception {
        // given
        given(calculatorService.calculate(anyString(), any(), any()))
                .willThrow(new InvalidCalculationException("Missing required parameter: b"));

        // when / then
        mockMvc.perform(get("/api/v1/calculator/add").param("a", "1"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void shouldReturn400WhenDividingByZero() throws Exception {
        // given
        given(calculatorService.calculate("divide", 1.0, 0.0))
                .willThrow(new InvalidCalculationException("Division by zero is not allowed"));

        // when / then
        mockMvc.perform(get("/api/v1/calculator/divide").param("a", "1").param("b", "0"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void shouldReturn400WhenSquareRootOfNegativeNumber() throws Exception {
        // given
        given(calculatorService.calculate(eq("sqrt"), eq(-4.0), any()))
                .willThrow(new InvalidCalculationException("Square root of a negative number is not allowed"));

        // when / then
        mockMvc.perform(get("/api/v1/calculator/sqrt").param("a", "-4"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void shouldReturn400WhenParameterAIsNotANumber() throws Exception {
        // when / then
        mockMvc.perform(get("/api/v1/calculator/add").param("a", "not-a-number").param("b", "2"))
                .andExpect(status().isBadRequest());
    }
}
