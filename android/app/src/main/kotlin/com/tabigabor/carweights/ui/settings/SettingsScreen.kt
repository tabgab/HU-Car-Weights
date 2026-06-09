package com.tabigabor.carweights.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tabigabor.carweights.ui.theme.Muted
import com.tabigabor.carweights.ui.theme.Panel
import com.tabigabor.carweights.ui.theme.Text

@Composable
fun SettingsScreen(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Settings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Data source", color = Text, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(4.dp))
                Text("cars.db is bundled in the app (read-only SQLite).",
                    color = Muted, fontSize = 12.sp)
            }
        }
        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Refresh data", color = Text, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(4.dp))
                Text("In-app download of a newer cars.db.gz (configured in a future release).",
                    color = Muted, fontSize = 12.sp)
            }
        }
        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("About", color = Text, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(4.dp))
                Text("Curb weights from cars-data.com and katalogus.hasznaltauto.hu.",
                    color = Muted, fontSize = 12.sp)
            }
        }
    }
}
