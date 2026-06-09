package com.tabigabor.carweights.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ViewList
import androidx.compose.material.icons.filled.Policy
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.tabigabor.carweights.AppState
import com.tabigabor.carweights.ui.browse.BrowseScreen
import com.tabigabor.carweights.ui.detail.CarDetailScreen
import com.tabigabor.carweights.ui.lookup.LookupScreen
import com.tabigabor.carweights.ui.policy.PolicyExplorerScreen
import com.tabigabor.carweights.ui.settings.SettingsScreen

enum class Tab(val label: String) {
    POLICY("Policy"),
    LOOKUP("Lookup"),
    BROWSE("Browse"),
    SETTINGS("Settings"),
}

@Composable
fun MainScreen(state: AppState) {
    var tab by rememberSaveable { mutableStateOf(Tab.POLICY) }
    Scaffold(
        bottomBar = {
            NavigationBar {
                Tab.values().forEach { t ->
                    NavigationBarItem(
                        selected = tab == t,
                        onClick = { tab = t },
                        icon = {
                            Icon(
                                when (t) {
                                    Tab.POLICY -> Icons.Filled.Policy
                                    Tab.LOOKUP -> Icons.Filled.Search
                                    Tab.BROWSE -> Icons.AutoMirrored.Filled.ViewList
                                    Tab.SETTINGS -> Icons.Filled.Settings
                                },
                                contentDescription = t.label,
                            )
                        },
                        label = { Text(t.label) },
                    )
                }
            }
        }
    ) { inner ->
        // When a car is selected (from Browse or Policy border cases), overlay the
        // detail screen on top of the current tab. Back clears selection.
        if (state.selectedCarId.value != null) {
            CarDetailScreen(state = state, modifier = Modifier.padding(inner))
        } else when (tab) {
            Tab.POLICY -> PolicyExplorerScreen(
                state = state, modifier = Modifier.padding(inner),
            )
            Tab.LOOKUP -> LookupScreen(
                state = state, modifier = Modifier.padding(inner),
            )
            Tab.BROWSE -> BrowseScreen(
                state = state, modifier = Modifier.padding(inner),
            )
            Tab.SETTINGS -> SettingsScreen(
                state = state, modifier = Modifier.padding(inner),
            )
        }
    }
}
