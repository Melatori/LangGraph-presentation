package com.example.calculatorservice.calculator;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
class CalculatorExceptionHandler {

    @ExceptionHandler(InvalidCalculationException.class)
    ProblemDetail handleInvalidCalculation(InvalidCalculationException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, ex.getMessage());
    }
}
