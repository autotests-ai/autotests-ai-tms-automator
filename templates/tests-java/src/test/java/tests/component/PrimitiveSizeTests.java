package tests.component;

import annotations.Layer;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import tests.TestBase;

import static com.codeborne.selenide.Condition.visible;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.executeJavaScript;
import static com.codeborne.selenide.Selenide.open;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@Layer("component")
@Tag("component")
@Epic("Component Catalog")
@Feature("Primitive sizes")
@DisplayName("Primitive sizes")
class PrimitiveSizeTests extends TestBase {

    private static final double SIZE_TOLERANCE_PX = 0.6;

    @BeforeEach
    void openCatalog() {
        open("/components.html");
        $("[data-testid='components-page']").shouldBe(visible);
    }

    @Test
    @DisplayName("Icons are 18px wide")
    void iconsAreEighteenPixels() {
        assertElementWidth("[data-testid='icon-lang']", 18);
        assertElementWidth("[data-testid='icon-github']", 18);
    }

    @Test
    @DisplayName("Icon buttons are 36px square")
    void iconButtonsAreThirtySixPixels() {
        assertElementSize("[data-testid='icon-btn-theme']", 36, 36);
        assertElementSize("[data-testid='icon-btn-github']", 36, 36);
    }

    @Test
    @DisplayName("Primary button min-height token is 36px")
    void primaryButtonMinHeightIsThirtySixPixels() {
        assertMinHeight("[data-testid='btn-primary']", 36);
        assertTrue(readHeight("[data-testid='btn-primary']") >= 36 - SIZE_TOLERANCE_PX);
    }

    @Test
    @DisplayName("Text input min-height token is 36px")
    void textInputMinHeightIsThirtySixPixels() {
        assertMinHeight("[data-testid='input-text']", 36);
        assertTrue(readHeight("[data-testid='input-text']") >= 36 - SIZE_TOLERANCE_PX);
    }

    @Test
    @DisplayName("Textarea min-height is at least 72px")
    void textareaMinHeightIsSeventyTwoPixels() {
        var height = readHeight("[data-testid='textarea-comment']");
        assertTrue(height >= 72 - SIZE_TOLERANCE_PX,
                "textarea height expected >= 72px, actual %.2f".formatted(height));
    }

    @Test
    @DisplayName("Checkbox box is 18px")
    void checkboxBoxIsEighteenPixels() {
        assertElementSize("[data-testid='checkbox-default'] .checkbox__input", 18, 18);
    }

    private static void assertElementWidth(String selector, double expected) {
        assertEquals(expected, readWidth(selector), SIZE_TOLERANCE_PX, selector + " width");
    }

    private static void assertElementHeight(String selector, double expected) {
        assertEquals(expected, readHeight(selector), SIZE_TOLERANCE_PX, selector + " height");
    }

    private static void assertMinHeight(String selector, double expected) {
        var minHeight = executeJavaScript(
                "return parseFloat(getComputedStyle(document.querySelector(arguments[0])).minHeight);",
                selector);
        assertEquals(expected, ((Number) minHeight).doubleValue(), SIZE_TOLERANCE_PX, selector + " min-height");
    }

    private static void assertElementSize(String selector, double expectedWidth, double expectedHeight) {
        var size = readSize(selector);
        assertEquals(expectedWidth, size[0], SIZE_TOLERANCE_PX, selector + " width");
        assertEquals(expectedHeight, size[1], SIZE_TOLERANCE_PX, selector + " height");
    }

  private static double readWidth(String selector) {
    return readSize(selector)[0];
  }

  private static double readHeight(String selector) {
    return readSize(selector)[1];
  }

    private static double[] readSize(String selector) {
        @SuppressWarnings("unchecked")
        List<Number> result = executeJavaScript(
                """
                const el = document.querySelector(arguments[0]);
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return [rect.width, rect.height];
                """,
                selector);
        return new double[] {result.get(0).doubleValue(), result.get(1).doubleValue()};
    }
}
