package com.tabigabor.carweights.ui.lookup

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tabigabor.carweights.data.CarsRepository
import com.tabigabor.carweights.domain.FeeClassifier
import com.tabigabor.carweights.domain.FeeStatus
import com.tabigabor.carweights.ui.theme.Amber
import com.tabigabor.carweights.ui.theme.Green
import com.tabigabor.carweights.ui.theme.Grey
import com.tabigabor.carweights.ui.theme.Muted
import com.tabigabor.carweights.ui.theme.Panel
import com.tabigabor.carweights.ui.theme.Red
import com.tabigabor.carweights.ui.theme.Text

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LookupScreen(@Suppress("UNUSED_PARAMETER") repository: CarsRepository, modifier: Modifier = Modifier) {
    var powertrain by remember { mutableStateOf("BEV") }
    var weightText by remember { mutableStateOf("1800") }

    val weight = weightText.toIntOrNull()
    val status = FeeClassifier.classify(powertrain, weight)
    val threshold = FeeClassifier.thresholdFor(powertrain)

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("Lookup", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("Quick answer: will this car pay double?",
            style = MaterialTheme.typography.bodySmall, color = Muted)

        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Powertrain", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(6.dp))
                val opts = listOf("BEV", "PHEV", "ICE")
                SingleChoiceSegmentedButtonRow {
                    opts.forEachIndexed { i, opt ->
                        SegmentedButton(
                            selected = powertrain == opt,
                            onClick = { powertrain = opt },
                            shape = SegmentedButtonDefaults.itemShape(i, opts.size),
                        ) { Text(opt) }
                    }
                }
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Text("Curb weight (kg)", fontWeight = FontWeight.SemiBold, color = Text)
                Spacer(Modifier.height(6.dp))
                OutlinedTextField(
                    value = weightText,
                    onValueChange = { weightText = it.filter { c -> c.isDigit() }.take(5) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                )
                if ((weight ?: 0) in 800..3000) {
                    Spacer(Modifier.height(8.dp))
                    Slider(
                        value = (weight ?: 0).coerceIn(800, 3000).toFloat(),
                        onValueChange = { weightText = it.toInt().toString() },
                        valueRange = 800f..3000f,
                    )
                }
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.padding(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        statusLabel(status),
                        color = statusColor(status),
                        fontWeight = FontWeight.Bold,
                        fontSize = 28.sp,
                    )
                    Spacer(Modifier.weight(1f))
                    Text("Threshold: $threshold kg", color = Muted, fontSize = 13.sp)
                }
                Spacer(Modifier.height(6.dp))
                Text(ruleText(powertrain, status, threshold, weight),
                    color = Text, fontSize = 13.sp)
            }
        }
    }
}

private fun statusLabel(s: FeeStatus): String = when (s) {
    FeeStatus.OK -> "OK"
    FeeStatus.DOUBLE -> "DOUBLE"
    FeeStatus.BORDERLINE -> "BORDERLINE"
    FeeStatus.UNKNOWN -> "UNKNOWN"
}

private fun statusColor(s: FeeStatus) = when (s) {
    FeeStatus.OK -> Green
    FeeStatus.DOUBLE -> Red
    FeeStatus.BORDERLINE -> Amber
    FeeStatus.UNKNOWN -> Grey
}

private fun ruleText(pt: String, s: FeeStatus, t: Int, w: Int?): String {
    if (w == null) return "Enter a weight to see the verdict."
    val margin = w - t
    return when (s) {
        FeeStatus.OK -> "$pt at $w kg is $margin kg under the $t kg limit — OK."
        FeeStatus.DOUBLE -> "$pt at $w kg is +$margin kg over the $t kg limit — pays double."
        FeeStatus.BORDERLINE -> "Range straddles the $t kg limit."
        FeeStatus.UNKNOWN -> "Weight unknown."
    }
}
