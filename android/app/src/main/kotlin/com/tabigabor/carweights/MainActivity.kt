package com.tabigabor.carweights

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.tabigabor.carweights.ui.MainScreen
import com.tabigabor.carweights.ui.theme.CarWeightsTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = application as CarWeightsApp
        setContent {
            CarWeightsTheme {
                MainScreen(repository = app.repository)
            }
        }
    }
}
