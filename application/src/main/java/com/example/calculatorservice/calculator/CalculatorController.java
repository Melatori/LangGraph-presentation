package com.example.calculatorservice.calculator;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/calculator")
class CalculatorController {

    private final CalculatorService calculatorService;

    CalculatorController(CalculatorService calculatorService) {
        this.calculatorService = calculatorService;
    }

    @GetMapping("/{operation}")
    CalculationResponse calculate(
            @PathVariable String operation,
            @RequestParam(required = false) Double a,
            @RequestParam(required = false) Double b) {
        return calculatorService.calculate(operation, a, b);
    }
}
