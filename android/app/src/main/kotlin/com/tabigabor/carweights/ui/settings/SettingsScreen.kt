package com.tabigabor.carweights.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tabigabor.carweights.AppState
import com.tabigabor.carweights.ui.theme.Muted
import com.tabigabor.carweights.ui.theme.Panel
import com.tabigabor.carweights.ui.theme.Panel2
import com.tabigabor.carweights.ui.theme.Text

@Composable
fun SettingsScreen(state: AppState, modifier: Modifier = Modifier) {
    val ctx = LocalContext.current
    val scale by state.fontScale
    val huOnly by state.huOnly

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Settings",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold)

        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Text size", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(4.dp))
                Text("Scales every text on every tab. Persists across launches.",
                    color = Muted, fontSize = 12.sp)
                Spacer(Modifier.height(10.dp))
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text("Aa", color = Muted, fontSize = 14.sp)
                    Text("Current: ${"%.2f".format(scale)}×",
                        color = Text, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    Text("Aa", color = Text, fontSize = 22.sp, fontWeight = FontWeight.SemiBold)
                }
                Spacer(Modifier.height(6.dp))
                Slider(
                    value = scale,
                    onValueChange = { state.setFontScale(ctx, it) },
                    valueRange = AppState.FONT_SCALE_CHOICES.first()..
                        AppState.FONT_SCALE_CHOICES.last(),
                    steps = AppState.FONT_SCALE_CHOICES.size - 2,
                    colors = SliderDefaults.colors(),
                )
                Spacer(Modifier.height(6.dp))
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    AppState.FONT_SCALE_CHOICES.forEach { s ->
                        val selected = kotlin.math.abs(s - scale) < 0.01f
                        FilterChip(
                            selected = selected,
                            onClick = { state.setFontScale(ctx, s) },
                            label = { Text("${"%.2f".format(s)}×") },
                        )
                    }
                }
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Data source", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(4.dp))
                Text(
                    "cars.db is bundled in the app (read-only SQLite). " +
                        "${state.cars.value.size.locs()} cars loaded.",
                    color = Muted, fontSize = 12.sp,
                )
                Spacer(Modifier.height(6.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("HU-catalog only", color = Text, fontSize = 14.sp)
                    Spacer(Modifier.weight(1f))
                    Switch(checked = huOnly, onCheckedChange = { state.setHuOnly(ctx, it) })
                }
                Text(
                    "Filter the fleet to variants with a Hungarian-katalógus weight.",
                    color = Muted, fontSize = 11.sp,
                )
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Refresh data", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(4.dp))
                Text("In-app download of a newer cars.db.gz (configured in a future release).",
                    color = Muted, fontSize = 12.sp)
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = Panel2)) {
            Column(Modifier.padding(14.dp)) {
                Text("About", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(4.dp))
                Text(
                    "Curb weights from cars-data.com and katalogus.hasznaltauto.hu. " +
                        "The default 2027 policy is BEV > 2000 kg, ICE/PHEV > 1800 kg.",
                    color = Muted, fontSize = 12.sp,
                )
            }
        }
    }
}

private fun Int.locs(): String = java.util.Locale.US.let { String.format(it, "%,d", this) }
