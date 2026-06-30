package helpers;

import java.util.List;

import static com.codeborne.selenide.Selenide.executeJavaScript;
import static org.junit.jupiter.api.Assertions.assertTrue;

public final class HeaderLayout {

    public static final int EXPECTED_GAP_PX = 16;
    public static final double GAP_TOLERANCE_PX = 0.6;

    public static final int EXPECTED_HEADER_HEIGHT_PX = 56;
    public static final double HEIGHT_TOLERANCE_PX = 1.5;

    public static final String MEASURE_INNER_CSS_GAP_SCRIPT = """
            const inner = document.querySelector('.header__inner');
            if (!inner) return null;
            return parseFloat(getComputedStyle(inner).columnGap);
            """;

    public static final String MEASURE_INNER_GAPS_SCRIPT = """
            const inner = document.querySelector('.header__inner');
            if (!inner) return [];
            const items = [...inner.children].filter((el) => {
              const style = getComputedStyle(el);
              return style.display !== 'none' && style.visibility !== 'hidden';
            });
            return items.slice(0, -1).map((el, i) => {
              const a = el.getBoundingClientRect();
              const b = items[i + 1].getBoundingClientRect();
              return Math.round((b.left - a.right) * 100) / 100;
            });
            """;

    public static final String MEASURE_HEADER_HEIGHT_SCRIPT = """
            const header = document.querySelector('[data-testid="header"]');
            if (!header) return null;
            return Math.round(header.getBoundingClientRect().height * 100) / 100;
            """;

    public static final String IS_ELEMENT_VISIBLE_SCRIPT = """
            const el = document.querySelector(arguments[0]);
            if (!el) return false;
            const style = getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') return false;
            return el.getBoundingClientRect().width > 0;
            """;

    private HeaderLayout() {
    }

    @SuppressWarnings("unchecked")
    public static List<? extends Number> readInnerGaps() {
        return executeJavaScript(MEASURE_INNER_GAPS_SCRIPT);
    }

    public static void assertCssGapNearCanonical(int viewportWidth) {
        var gap = executeJavaScript(MEASURE_INNER_CSS_GAP_SCRIPT);
        if (gap == null) {
            throw new AssertionError(".header__inner missing at %dpx viewport".formatted(viewportWidth));
        }

        var actual = ((Number) gap).doubleValue();
        if (Math.abs(actual - EXPECTED_GAP_PX) > GAP_TOLERANCE_PX) {
            throw new AssertionError(
                    "Header inner CSS gap drift at %dpx: expected %dpx, actual %.2f"
                            .formatted(viewportWidth, EXPECTED_GAP_PX, actual));
        }
    }

    public static void assertUniformGaps(List<? extends Number> gaps, int viewportWidth) {
        if (gaps.isEmpty()) {
            throw new AssertionError("No gaps measured on .header__inner at %dpx viewport".formatted(viewportWidth));
        }

        var min = gaps.stream().mapToDouble(Number::doubleValue).min().orElseThrow();
        var max = gaps.stream().mapToDouble(Number::doubleValue).max().orElseThrow();

        if (max - min > GAP_TOLERANCE_PX) {
            throw new AssertionError(
                    "Header inner gaps are uneven at %dpx: min=%.2f max=%.2f values=%s"
                            .formatted(viewportWidth, min, max, gaps));
        }

        if (Math.abs(min - EXPECTED_GAP_PX) > GAP_TOLERANCE_PX
                || Math.abs(max - EXPECTED_GAP_PX) > GAP_TOLERANCE_PX) {
            throw new AssertionError(
                    "Header inner gaps drift from %dpx at %dpx viewport: min=%.2f max=%.2f values=%s"
                            .formatted(EXPECTED_GAP_PX, viewportWidth, min, max, gaps));
        }
    }

    public static void assertHeaderHeightNearCanonical(int viewportWidth) {
        var height = executeJavaScript(MEASURE_HEADER_HEIGHT_SCRIPT);
        if (height == null) {
            throw new AssertionError("Header element missing at %dpx viewport".formatted(viewportWidth));
        }

        var actual = ((Number) height).doubleValue();
        if (Math.abs(actual - EXPECTED_HEADER_HEIGHT_PX) > HEIGHT_TOLERANCE_PX) {
            throw new AssertionError(
                    "Header height drift at %dpx: expected ~%dpx, actual %.2f"
                            .formatted(viewportWidth, EXPECTED_HEADER_HEIGHT_PX, actual));
        }
    }

    public static void assertNavAndSearchVisible(boolean expectedVisible, int viewportWidth) {
        assertElementVisible("[data-testid='header-nav']", expectedVisible, "nav", viewportWidth);
        assertElementVisible("[data-testid='header-search']", expectedVisible, "search", viewportWidth);
    }

    private static void assertElementVisible(String selector, boolean expectedVisible, String name, int viewportWidth) {
        var visible = Boolean.TRUE.equals(executeJavaScript(IS_ELEMENT_VISIBLE_SCRIPT, selector));
        assertTrue(
                visible == expectedVisible,
                () -> "Header %s must be %s at %dpx viewport".formatted(
                        name,
                        expectedVisible ? "visible" : "hidden",
                        viewportWidth));
    }
}
