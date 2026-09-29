package com.example.calculatorservice.calculator;

/**
 * Thrown when a calculation request is invalid: an unknown operation, a missing
 * parameter, division by zero or the square root of a negative number.
 */
public class InvalidCalculationException extends RuntimeException {

    public InvalidCalculationException(String message) {
        super(message);
    }
}
