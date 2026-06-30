package tests.component;

import annotations.Layer;
import io.qameta.allure.Epic;
import io.qameta.allure.Feature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import tests.TestBase;

import java.util.List;

import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Condition.visible;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.executeJavaScript;
import static com.codeborne.selenide.Selenide.open;
import static org.junit.jupiter.api.Assertions.assertEquals;

@Layer("component")
@Tag("component")
@Epic("Component Catalog")
@Feature("Lang toggle")
@DisplayName("Lang toggle")
class LangToggleTests extends TestBase {

    private static final double SIZE_TOLERANCE_PX = 0.6;

    @BeforeEach
    void openCatalog() {
        open("/components.html");
        $("[data-testid='section-lang-toggle']").shouldBe(visible);
    }

    @Test
    @DisplayName("Lang toggle button hit area is 36px")
    void langToggleButtonIsThirtySixPixels() {
        var size = readSize("[data-testid='lang-toggle-btn']");
        assertEquals(36, size[0], SIZE_TOLERANCE_PX, "lang-toggle width");
        assertEquals(36, size[1], SIZE_TOLERANCE_PX, "lang-toggle height");
    }

    @Test
    @DisplayName("Lang toggle icon is 18px and label shows RU")
    void langToggleIconAndLabel() {
        var iconSize = readSize("[data-testid='lang-toggle'] .icon");
        assertEquals(18, iconSize[0], SIZE_TOLERANCE_PX, "lang-toggle icon width");
        assertEquals(18, iconSize[1], SIZE_TOLERANCE_PX, "lang-toggle icon height");
        $("[data-testid='lang-toggle-label']").shouldHave(text("RU"));
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
