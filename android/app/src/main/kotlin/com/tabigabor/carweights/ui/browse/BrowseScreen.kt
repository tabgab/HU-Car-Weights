package com.tabigabor.carweights.ui.browse

import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tabigabor.carweights.data.CarsRepository
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

@Composable
fun BrowseScreen(repository: CarsRepository, modifier: Modifier = Modifier) {
    val all = remember { runCatching { repository.loadAll() }.getOrElse { emptyList() } }
    var q by remember { mutableStateOf("") }
    val filtered = remember(all, q) {
        if (q.isBlank()) all
        else all.filter { c ->
            c.make.contains(q, true) || c.model.contains(q, true) ||
                (c.trim?.contains(q, true) == true)
        }
    }

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
        Text("${filtered.size} / ${all.size} cars", color = Muted, fontSize = 12.sp)
        Spacer(Modifier.height(8.dp))
        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            items(filtered.take(500), key = { it.id }) { c -> CarRow(c) }
        }
    }
}

@Composable
private fun CarRow(c: Car) {
    val status = FeeClassifier.classify(c.powertrainType, c.weight, c.weightMin, c.weightMax)
    val w = c.weight ?: c.weightMin ?: c.weightMax
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Row(
            Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("${c.make} ${c.model}", color = Text, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
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
