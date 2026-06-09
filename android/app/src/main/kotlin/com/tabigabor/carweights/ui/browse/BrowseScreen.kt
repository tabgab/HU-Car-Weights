package com.tabigabor.carweights.ui.browse

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
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
import com.tabigabor.carweights.ui.theme.Red
import com.tabigabor.carweights.ui.theme.Text

private const val VISIBLE_LIMIT = 500

@Composable
fun BrowseScreen(state: AppState, modifier: Modifier = Modifier) {
    val ctx = LocalContext.current
    val all by state.cars
    val huOnly by state.huOnly
    var q by rememberSaveable { mutableStateOf("") }

    val visible = remember(all, q, huOnly) {
        val base = if (huOnly) all.filter { it.huWeightKg != null } else all
        if (q.isBlank()) base
        else base.filter { c ->
            c.make.contains(q, true) || c.model.contains(q, true) ||
                (c.trim?.contains(q, true) == true)
        }
    }
    val shown = visible.take(VISIBLE_LIMIT)

    Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
        Text("Browse", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = q,
            onValueChange = { q = it },
            placeholder = { Text("Search make / model / trim") },
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("HU-catalog only", color = Text, fontSize = 14.sp)
            Spacer(Modifier.width(8.dp))
            Switch(
                checked = huOnly,
                onCheckedChange = { state.setHuOnly(ctx, it) },
            )
        }
        Spacer(Modifier.height(4.dp))
        val totalLabel = if (visible.size > VISIBLE_LIMIT) {
            "${VISIBLE_LIMIT} of ${visible.size.locs()}"
        } else {
            "${visible.size.locs()} of ${all.size.locs()}"
        }
        Text("$totalLabel cars", color = Muted, fontSize = 12.sp)
        Spacer(Modifier.height(8.dp))
        if (shown.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No cars match.", color = Muted)
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                items(shown, key = { it.id }) { c ->
                    CarRow(c, onClick = { state.selectedCarId.value = c.id })
                }
            }
        }
    }
}

@Composable
private fun CarRow(c: Car, onClick: () -> Unit) {
    val status = FeeClassifier.classify(c.powertrainType, c.weight, c.weightMin, c.weightMax)
    val w = c.weight ?: c.weightMin ?: c.weightMax
    Card(
        colors = CardDefaults.cardColors(containerColor = Panel),
        modifier = Modifier.clickable { onClick() },
    ) {
        Row(
            Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("${c.make} ${c.model}",
                    color = Text, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                Text(
                    listOfNotNull(c.trim, c.powertrainType, c.drivetrain, c.modelYear?.toString())
                        .joinToString(" · "),
                    color = Muted, fontSize = 11.sp,
                )
            }
            if (w != null) {
                Text("$w kg", color = Text, fontSize = 13.sp)
                Spacer(Modifier.width(8.dp))
            }
            StatusPill(status)
        }
    }
}

@Composable
private fun StatusPill(s: FeeStatus) {
    val (label, color) = when (s) {
        FeeStatus.OK -> "OK" to Green
        FeeStatus.DOUBLE -> "DOUBLE" to Red
        FeeStatus.BORDERLINE -> "BORDER" to Amber
        FeeStatus.UNKNOWN -> "?" to Grey
    }
    Text(
        label,
        color = color,
        fontSize = 11.sp,
        fontWeight = FontWeight.Bold,
        modifier = Modifier
            .clip(RoundedCornerShape(10.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp),
    )
}

private fun Int.locs(): String = java.util.Locale.US.let { String.format(it, "%,d", this) }
