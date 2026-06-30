package helpers;

import annotations.Layer;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@Layer("unit")
@DisplayName("TokensCss")
class TokensCssTest {

    @ParameterizedTest
    @MethodSource("canonicalSizeTokens")
    @DisplayName("tokens.css keeps canonical component size tokens")
    void tokensMatchComponentSizesCanon(String token, String expected) throws Exception {
        var tokens = TokensCss.parseRootTokens(TokensCss.defaultTokensPath());
        assertTrue(tokens.containsKey(token), "Missing token: " + token);
        assertEquals(expected, tokens.get(token));
    }

    static Stream<Arguments> canonicalSizeTokens() {
        return Stream.of(
                Arguments.of("--control-height-md", "36px"),
                Arguments.of("--icon-size-md", "18px"),
                Arguments.of("--input-min-width", "200px"),
                Arguments.of("--header-height", "56px")
        );
    }
}
