package helpers;

import annotations.Layer;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@Layer("unit")
@DisplayName("ScreenshotBaseline assets")
class ScreenshotBaselineAssetsTest {

  @ParameterizedTest
  @MethodSource("baselineCases")
  @DisplayName("baseline PNG exists and is readable")
  void baselinePngExists(String area, int viewport) throws Exception {
    var resource = "screenshots/" + area + "/" + viewport + ".png";
    var url = Thread.currentThread().getContextClassLoader().getResource(resource);
    if (url != null) {
      try (InputStream in = url.openStream()) {
        assertNotNull(in.readNBytes(8));
      }
      return;
    }

    var path = Path.of("src", "test", "resources", "screenshots", area, viewport + ".png");
    assertTrue(Files.isRegularFile(path), "Baseline missing: " + path);
    assertTrue(Files.size(path) > 0, "Baseline empty: " + path);
  }

  static Stream<Arguments> baselineCases() {
    return Stream.of(
        Arguments.of("header", 390),
        Arguments.of("header", 768),
        Arguments.of("header", 1280),
        Arguments.of("login", 390),
        Arguments.of("login", 768),
        Arguments.of("login", 1280),
        Arguments.of("logged-in", 390),
        Arguments.of("logged-in", 768),
        Arguments.of("logged-in", 1280)
    );
  }
}
