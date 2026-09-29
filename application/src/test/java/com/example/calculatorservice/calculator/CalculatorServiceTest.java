package com.example.calculatorservice.calculator;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class CalculatorServiceTest {

    private final CalculatorService calculatorService = new CalculatorService();

    @Test
    void shouldAddTwoNumbers() {
        // given
        String operation = "add";

        // when
        CalculationResponse response = calculatorService.calculate(operation, 2.0, 3.0);

        // then
        assertThat(response.result()).isEqualTo(5.0);
    }

    @Test
    void shouldSubtractTwoNumbers() {
        // given
        String operation = "subtract";

        // when
        CalculationResponse response = calculatorService.calculate(operation, 5.0, 3.0);

        // then
        assertThat(response.result()).isEqualTo(2.0);
    }

    @Test
    void shouldMultiplyTwoNumbers() {
        // given
        String operation = "multiply";

        // when
        CalculationResponse response = calculatorService.calculate(operation, 4.0, 3.0);

        // then
        assertThat(response.result()).isEqualTo(12.0);
    }

    @Test
    void shouldDivideTwoNumbers() {
        // given
        String operation = "divide";

        // when
        CalculationResponse response = calculatorService.calculate(operation, 6.0, 3.0);

        // then
        assertThat(response.result()).isEqualTo(2.0);
    }

    @Test
    void shouldThrowWhenDividingByZero() {
        // given
        String operation = "divide";

        // when / then
        assertThatThrownBy(() -> calculatorService.calculate(operation, 6.0, 0.0))
                .isInstanceOf(InvalidCalculationException.class);
    }

    @Test
    void shouldRaiseToPower() {
        // given
        String operation = "power";

        // when
        CalculationResponse response = calculatorService.calculate(operation, 2.0, 3.0);

        // then
        assertThat(response.result()).isEqualTo(8.0);
    }

    @Test
    void shouldComputeSquareRoot() {
        // given
        String operation = "sqrt";

        // when
        CalculationResponse response = calculatorService.calculate(operation, 9.0, null);

        // then
        assertThat(response.result()).isEqualTo(3.0);
    }

    @Test
    void shouldThrowWhenSquareRootOfNegativeNumber() {
        // given
        String operation = "sqrt";

        // when / then
        assertThatThrownBy(() -> calculatorService.calculate(operation, -9.0, null))
                .isInstanceOf(InvalidCalculationException.class);
    }

    @Test
    void shouldThrowWhenOperationIsUnknown() {
        // given
        String operation = "modulo";

        // when / then
        assertThatThrownBy(() -> calculatorService.calculate(operation, 1.0, 2.0))
                .isInstanceOf(InvalidCalculationException.class);
    }

    @Test
    void shouldThrowWhenParameterAIsMissing() {
        // given
        String operation = "add";

        // when / then
        assertThatThrownBy(() -> calculatorService.calculate(operation, null, 2.0))
                .isInstanceOf(InvalidCalculationException.class);
    }

    @Test
    void shouldThrowWhenParameterBIsMissingForNonSqrtOperation() {
        // given
        String operation = "add";

        // when / then
        assertThatThrownBy(() -> calculatorService.calculate(operation, 1.0, null))
                .isInstanceOf(InvalidCalculationException.class);
    }
}
