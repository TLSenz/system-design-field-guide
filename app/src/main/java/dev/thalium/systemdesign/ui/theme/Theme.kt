package dev.thalium.systemdesign.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val Ink = Color(0xFFE8E3D9)
val Muted = Color(0xFFA7B0BA)
val Copper = Color(0xFFC9A97C)
val Sage = Color(0xFF9DB4A0)
val Deep = Color(0xFF0F1216)
val Panel = Color(0xFF161B22)
val PanelRaised = Color(0xFF1E252E)

private val DarkScheme = darkColorScheme(
    primary = Copper,
    onPrimary = Color(0xFF241A0B),
    primaryContainer = Color(0xFF3A2E1D),
    onPrimaryContainer = Color(0xFFF2E2C8),
    secondary = Sage,
    onSecondary = Color(0xFF102015),
    secondaryContainer = Color(0xFF253429),
    onSecondaryContainer = Color(0xFFD7E6D9),
    tertiary = Color(0xFFA8B6C8),
    onTertiary = Color(0xFF101820),
    background = Deep,
    onBackground = Ink,
    surface = Panel,
    onSurface = Ink,
    surfaceVariant = PanelRaised,
    onSurfaceVariant = Muted,
    outline = Color(0xFF2C353F),
    outlineVariant = Color(0xFF222A33),
    error = Color(0xFFE07A6A),
    onError = Color(0xFF2A0E0A)
)

private val LightScheme = lightColorScheme(
    primary = Color(0xFF8A6A3B),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFF0E2CB),
    onPrimaryContainer = Color(0xFF2C2011),
    secondary = Color(0xFF526A57),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFDCE8DD),
    onSecondaryContainer = Color(0xFF15251A),
    background = Color(0xFFFAF7F1),
    onBackground = Color(0xFF1B1A17),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF1B1A17),
    surfaceVariant = Color(0xFFF0EBE1),
    onSurfaceVariant = Color(0xFF5C6169),
    outline = Color(0xFFD9D2C4),
    outlineVariant = Color(0xFFE7E1D5),
    error = Color(0xFFA63D2E),
    onError = Color(0xFFFFFFFF)
)

private val AppTypography = Typography(
    displaySmall = TextStyle(
        fontFamily = FontFamily.Serif,
        fontWeight = FontWeight.Normal,
        fontSize = 34.sp,
        lineHeight = 40.sp,
        letterSpacing = (-0.5).sp
    ),
    headlineMedium = TextStyle(
        fontFamily = FontFamily.Serif,
        fontWeight = FontWeight.Normal,
        fontSize = 26.sp,
        lineHeight = 32.sp
    ),
    headlineSmall = TextStyle(
        fontFamily = FontFamily.Serif,
        fontWeight = FontWeight.Medium,
        fontSize = 21.sp,
        lineHeight = 27.sp
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.Serif,
        fontWeight = FontWeight.Medium,
        fontSize = 20.sp,
        lineHeight = 27.sp
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 15.sp,
        lineHeight = 21.sp
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 26.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 22.sp
    ),
    bodySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 13.sp,
        lineHeight = 19.sp
    ),
    labelLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 13.sp,
        letterSpacing = 0.4.sp
    ),
    labelSmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 10.sp,
        letterSpacing = 1.2.sp
    )
)

@Composable
fun SystemDesignTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkScheme else LightScheme,
        typography = AppTypography,
        content = content
    )
}
