package com.tabigabor.carweights.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColors = darkColorScheme(
    primary = Accent,
    background = Bg,
    surface = Panel,
    surfaceVariant = Panel2,
    onBackground = Text,
    onSurface = Text,
    onPrimary = Text,
    outline = Line,
    error = Red,
)

@Composable
fun CarWeightsTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = DarkColors, content = content)
}
