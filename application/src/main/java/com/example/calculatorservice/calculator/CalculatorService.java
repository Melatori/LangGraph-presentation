package com.example.calculatorservice.calculator;

import java.util.Locale;
import org.springframework.stereotype.Service;

@Service
class CalculatorService {

    CalculationResponse calculate(String operation, Double a, Double b) {
        Operation op = parseOperation(operation);
        validateParameters(op, a, b);
        double result = switch (op) {
            case ADD -> a + b;
            case SUBTRACT -> a - b;
            case MULTIPLY -> a * b;
            case DIVIDE -> divide(a, b);
            case POWER -> Math.pow(a, b);
            case SQRT -> sqrt(a);
        };
        return new CalculationResponse(result);
    }

    private Operation parseOperation(String operation) {
        try {
            return Operation.valueOf(operation.toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            throw new InvalidCalculationException("Unknown operation: " + operation);
        }
    }

    private void validateParameters(Operation operation, Double a, Double b) {
        if (a == null) {
            throw new InvalidCalculationException("Missing required parameter: a");
        }
        if (operation != Operation.SQRT && b == null) {
            throw new InvalidCalculationException("Missing required parameter: b");
        }
    }

    private double divide(double a, double b) {
        if (b == 0) {
            throw new InvalidCalculationException("Division by zero is not allowed");
        }
        return a / b;
    }

    private double sqrt(double a) {
        if (a < 0) {
            throw new InvalidCalculationException("Square root of a negative number is not allowed");
        }
        return Math.sqrt(a);
    }
}
