package com.tabigabor.carweights.ui.detail

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.LocalGasStation
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tabigabor.carweights.AppState
import com.tabigabor.carweights.domain.Car
import com.tabigabor.carweights.domain.FeeClassifier
import com.tabigabor.carweights.domain.FeeStatus
import com.tabigabor.carweights.ui.theme.Amber
import com.tabigabor.carweights.ui.theme.Green
import com.tabigabor.carweights.ui.theme.Grey
import com.tabigabor.carweights.ui.theme.Muted
import com.tabigabor.carweights.ui.theme.Panel
import com.tabigabor.carweights.ui.theme.Panel2
import com.tabigabor.carweights.ui.theme.Red
import com.tabigabor.carweights.ui.theme.Text

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CarDetailScreen(state: AppState, modifier: Modifier = Modifier) {
    val id by state.selectedCarId
    val car = id?.let { selectedId -> state.cars.value.firstOrNull { it.id == selectedId } }

    // Consume the system back press: close the detail, not the whole app.
    BackHandler(enabled = id != null) {
        state.selectedCarId.value = null
    }

    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        if (car != null) "${car.make} ${car.model}" else "Car detail",
                        fontWeight = FontWeight.SemiBold,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = { state.selectedCarId.value = null }) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Panel,
                    titleContentColor = Text,
                    navigationIconContentColor = Text,
                ),
            )
        }
    ) { inner ->
        Box(
            Modifier
                .fillMaxSize()
                .padding(inner)
        ) {
            if (car == null) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Pick a car from Browse or the Policy border cases.",
                        color = Muted, fontSize = 14.sp)
                }
            } else {
                CarDetailContent(car)
            }
        }
    }
}

@Composable
private fun CarDetailContent(c: Car) {
    val status = FeeClassifier.classify(c.powertrainType, c.weight, c.weightMin, c.weightMax)
    val threshold = FeeClassifier.thresholdFor(c.powertrainType)
    val w = c.weight ?: c.weightMin ?: c.weightMax
    val margin = if (w != null) w - threshold else null
    val isEv = c.powertrainType == "BEV"

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        // Hero: fee pill
        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        if (isEv) Icons.Filled.Bolt else Icons.Filled.LocalGasStation,
                        contentDescription = null,
                        tint = if (isEv) Green else Red,
                        modifier = Modifier.size(22.dp),
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(c.powertrainType, color = Muted, fontSize = 14.sp)
                }
                Spacer(Modifier.height(6.dp))
                Text(
                    c.trim?.let { "${c.make} ${c.model} · $it" } ?: "${c.make} ${c.model}",
                    color = Text, fontSize = 22.sp, fontWeight = FontWeight.Bold,
                )
                Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    FeePillBig(status)
                    Spacer(Modifier.width(12.dp))
                    Text("Threshold: $threshold kg", color = Muted, fontSize = 13.sp)
                }
                if (margin != null) {
                    Spacer(Modifier.height(4.dp))
                    Text(
                        when (status) {
                            FeeStatus.DOUBLE -> "Pays double — ${margin}kg over the $threshold kg threshold"
                            FeeStatus.OK -> "OK — $margin kg under the $threshold kg threshold"
                            FeeStatus.BORDERLINE -> "Range straddles the $threshold kg threshold"
                            FeeStatus.UNKNOWN -> "No published curb weight"
                        },
                        color = Muted, fontSize = 12.sp,
                    )
                }
            }
        }

        // Specs
        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Specifications", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(8.dp))
                Spec("Powertrain", c.powertrainType)
                Spec("Sub-type", c.powertrainSubtype ?: "—")
                Spec("Drivetrain", c.drivetrain ?: "—")
                Spec("Power", c.powerKw?.let { "$it kW" } ?: "—")
                Spec("Battery", c.batteryKwh?.let { "$it kWh" } ?: "—")
                Spec("Model year", c.modelYear?.toString() ?: "—")
            }
        }

        // Weight details (cars-data + HU)
        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Curb weight", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(8.dp))
                Spec(
                    "cars-data.com",
                    when {
                        c.weight != null && c.weightMin != null && c.weightMax != null &&
                            c.weightMin != c.weightMax -> "${fmt(c.weight)} kg  (${fmt(c.weightMin)}–${fmt(c.weightMax)} kg range)"
                        c.weight != null -> "${fmt(c.weight)} kg"
                        c.weightMin != null || c.weightMax != null -> "${fmt(c.weightMin)}–${fmt(c.weightMax)} kg"
                        else -> "—"
                    },
                )
                Spec("Hungarian katalógus", c.huWeightKg?.let { "$it kg" } ?: "—")
                if (c.huWeightKg != null && c.weight != null && c.huWeightKg != c.weight) {
                    val delta = c.huWeightKg - c.weight!!
                    val sign = if (delta > 0) "+" else ""
                    Text(
                        "Sources disagree by ${sign}${delta} kg — HU catalog is authoritative.",
                        color = Amber, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                    )
                } else                 if (c.huWeightKg != null && c.weight != null) {
                    Text(
                        "Sources agree (${fmt(c.weight)} kg).",
                        color = Green, fontSize = 12.sp,
                    )
                }
                Spec("Primary source", c.weightSource ?: "cars-data")
            }
        }

        // Fee rule
        Card(colors = CardDefaults.cardColors(containerColor = Panel2)) {
            Column(Modifier.padding(14.dp)) {
                Text(
                    "Rule (2027): ${if (isEv) "BEV" else "ICE / PHEV / HEV"} over $threshold kg → double Budapest parking fee.",
                    color = Muted, fontSize = 12.sp,
                )
            }
        }
    }
}

@Composable
private fun FeePillBig(s: FeeStatus) {
    val (label, color) = when (s) {
        FeeStatus.OK -> "OK" to Green
        FeeStatus.DOUBLE -> "DOUBLE" to Red
        FeeStatus.BORDERLINE -> "BORDERLINE" to Amber
        FeeStatus.UNKNOWN -> "UNKNOWN" to Grey
    }
    Text(
        label,
        color = color,
        fontSize = 18.sp,
        fontWeight = FontWeight.Bold,
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .padding(horizontal = 12.dp, vertical = 4.dp),
    )
}

@Composable
private fun Spec(label: String, value: String) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, color = Muted, fontSize = 13.sp)
        Text(value, color = Text, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

private fun fmt(v: Int?): String =
    v?.let { String.format(java.util.Locale.US, "%,d", it) } ?: "—"
