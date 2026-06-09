package com.tabigabor.carweights

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import com.tabigabor.carweights.ui.MainScreen
import com.tabigabor.carweights.ui.theme.CarWeightsTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val state = (application as CarWeightsApp).state
        setContent {
            CarWeightsTheme {
                val scale by state.fontScale
                val base = LocalDensity.current
                CompositionLocalProvider(
                    LocalDensity provides Density(base.density, scale)
                ) {
                    MainScreen(state = state)
                }
            }
        }
    }
}
