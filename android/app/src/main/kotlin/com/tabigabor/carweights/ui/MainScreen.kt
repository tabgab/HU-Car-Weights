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
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.tabigabor.carweights.data.CarsRepository
import com.tabigabor.carweights.ui.lookup.LookupScreen
import com.tabigabor.carweights.ui.policy.PolicyExplorerScreen
import com.tabigabor.carweights.ui.settings.SettingsScreen
import com.tabigabor.carweights.ui.browse.BrowseScreen

enum class Tab(val label: String) {
    POLICY("Policy"),
    LOOKUP("Lookup"),
    BROWSE("Browse"),
    SETTINGS("Settings"),
}

@Composable
fun MainScreen(repository: CarsRepository) {
    var tab by remember { mutableStateOf(Tab.POLICY) }
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
        when (tab) {
            Tab.POLICY -> PolicyExplorerScreen(repository = repository, modifier = Modifier.padding(inner))
            Tab.LOOKUP -> LookupScreen(repository = repository, modifier = Modifier.padding(inner))
            Tab.BROWSE -> BrowseScreen(repository = repository, modifier = Modifier.padding(inner))
            Tab.SETTINGS -> SettingsScreen(modifier = Modifier.padding(inner))
        }
    }
}
