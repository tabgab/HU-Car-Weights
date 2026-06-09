package com.tabigabor.carweights.ui.policy

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.LocalGasStation
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tabigabor.carweights.AppState
import com.tabigabor.carweights.data.PolicySimulator
import com.tabigabor.carweights.domain.Car
import com.tabigabor.carweights.domain.CarDecision
import com.tabigabor.carweights.domain.FeeClassifier
import com.tabigabor.carweights.domain.FeeStatus
import com.tabigabor.carweights.domain.Policy
import com.tabigabor.carweights.domain.PolicyOutcome
import com.tabigabor.carweights.ui.theme.Amber
import com.tabigabor.carweights.ui.theme.Green
import com.tabigabor.carweights.ui.theme.Grey
import com.tabigabor.carweights.ui.theme.Line
import com.tabigabor.carweights.ui.theme.Muted
import com.tabigabor.carweights.ui.theme.Panel
import com.tabigabor.carweights.ui.theme.Panel2
import com.tabigabor.carweights.ui.theme.Red
import com.tabigabor.carweights.ui.theme.Text

private const val MIN_THR = 1000
private const val MAX_THR = 3000
private const val STEP = 25

private fun Int.locs(): String = java.util.Locale.US.let { String.format(it, "%,d", this) }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PolicyExplorerScreen(
    state: AppState,
    modifier: Modifier = Modifier,
) {
    val ctx = LocalContext.current
    val cars by state.cars
    val isLoading by state.isLoading
    val loadError by state.loadError
    val huOnly by state.huOnly
    val ptFilter by state.powertrainFilter
    val makeFilter by state.makeFilter

    var policy by remember { mutableStateOf(Policy()) }
    var resetTick by remember { mutableStateOf(0) }
    var lastHuOnly by remember { mutableStateOf(huOnly) }
    if (lastHuOnly != huOnly) {
        lastHuOnly = huOnly
        policy = Policy()
        resetTick++
    }

    val filtered = remember(cars, huOnly, ptFilter, makeFilter, resetTick) {
        applyAllFilters(cars, huOnly, ptFilter, makeFilter)
    }
    val outcome = remember(filtered, policy, resetTick) { PolicySimulator.run(filtered, policy) }

    val allMakes = remember(cars) { cars.map { it.make }.distinct().sorted() }
    var makeSheetOpen by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Header()
        FilterCard(
            ptFilter = ptFilter,
            onPtChange = { state.setPowertrainFilter(ctx, it) },
            makeFilter = makeFilter,
            onMakeChange = { state.setMakeFilter(ctx, it) },
            onOpenMakePicker = { makeSheetOpen = true },
            onClearMakes = { state.setMakeFilter(ctx, emptySet()) },
            activeMakeCount = if (makeFilter.isEmpty()) 0 else makeFilter.size,
        )
        ThresholdCard(
            icon = Icons.Filled.Bolt,
            title = "BEV (electric) threshold",
            color = Green,
            value = policy.bevThresholdKg,
            onChange = { policy = policy.copy(bevThresholdKg = it) },
        )
        ThresholdCard(
            icon = Icons.Filled.LocalGasStation,
            title = "ICE / PHEV / HEV threshold",
            color = Red,
            value = policy.combustionThresholdKg,
            onChange = { policy = policy.copy(combustionThresholdKg = it) },
        )
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.End,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            val defaults = remember { Policy() }
            val atDefaults = policy == defaults
            TextButton(
                onClick = {
                    policy = Policy()
                    resetTick++
                },
                enabled = !atDefaults,
            ) {
                Icon(Icons.Filled.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(6.dp))
                Text("Reset to defaults (2000 / 1800)")
            }
        }
        when {
            loadError != null -> ErrorCard(loadError!!)
            isLoading -> LoadingCard()
            else -> {
                DistributionCard(outcome, filtered.size)
                BorderCasesCard(
                    outcome = outcome,
                    onOpenCar = { id -> state.selectedCarId.value = id },
                )
            }
        }
        NoteCard(policy)
    }

    if (makeSheetOpen) {
        val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ModalBottomSheet(
            onDismissRequest = { makeSheetOpen = false },
            sheetState = sheetState,
            containerColor = Panel,
        ) {
            MakePickerSheet(
                allMakes = allMakes,
                selected = makeFilter,
                onApply = { picked ->
                    state.setMakeFilter(ctx, picked)
                    makeSheetOpen = false
                },
                onClear = { state.setMakeFilter(ctx, emptySet()) },
            )
        }
    }
}

private fun applyAllFilters(
    all: List<Car>,
    huOnly: Boolean,
    ptFilter: Set<String>,
    makeFilter: Set<String>,
): List<Car> {
    if (!huOnly && ptFilter.isEmpty() && makeFilter.isEmpty()) return all
    return all.asSequence().filter { c ->
        (!huOnly || c.huWeightKg != null) &&
            (ptFilter.isEmpty() || c.powertrainSubtype in ptFilter) &&
            (makeFilter.isEmpty() || c.make in makeFilter)
    }.toList()
}

@Composable
private fun Header() {
    Column {
        Text(
            "Policy Explorer",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            "Drag the thresholds. See in real time which cars would pay double, and which are border cases.",
            style = MaterialTheme.typography.bodySmall,
            color = Muted,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
private fun FilterCard(
    ptFilter: Set<String>,
    onPtChange: (Set<String>) -> Unit,
    makeFilter: Set<String>,
    onMakeChange: (Set<String>) -> Unit,
    onOpenMakePicker: () -> Unit,
    onClearMakes: () -> Unit,
    activeMakeCount: Int,
) {
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Column(Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Filled.Tune, contentDescription = null,
                    tint = Accent, modifier = Modifier.size(18.dp),
                )
                Spacer(Modifier.width(6.dp))
                Text("Filter", fontWeight = FontWeight.SemiBold, color = Text, fontSize = 14.sp)
            }
            Spacer(Modifier.height(8.dp))
            Text("Powertrain", color = Muted, fontSize = 12.sp)
            Spacer(Modifier.height(4.dp))
            androidx.compose.foundation.layout.FlowRow(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                AppState.POWERTRAIN_FILTER_OPTIONS.forEach { opt ->
                    val on = opt in ptFilter
                    FilterChip(
                        selected = on,
                        onClick = {
                            val next = if (on) ptFilter - opt else ptFilter + opt
                            onPtChange(next)
                        },
                        label = { Text(opt) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Accent,
                            selectedLabelColor = Text,
                        ),
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
            Text("Make", color = Muted, fontSize = 12.sp)
            Spacer(Modifier.height(4.dp))
            androidx.compose.foundation.layout.FlowRow(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                AppState.TOP_MAKES.forEach { m ->
                    val on = m in makeFilter
                    FilterChip(
                        selected = on,
                        onClick = {
                            val next = if (on) makeFilter - m else makeFilter + m
                            onMakeChange(next)
                        },
                        label = { Text(m) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Accent,
                            selectedLabelColor = Text,
                        ),
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                TextButton(onClick = onOpenMakePicker) {
                    val label = if (activeMakeCount == 0) "All makes"
                        else if (activeMakeCount == 1) "1 make"
                        else "$activeMakeCount makes"
                    Text("Pick: $label →")
                }
                if (activeMakeCount > 0) {
                    TextButton(onClick = onClearMakes) { Text("Clear") }
                }
            }
        }
    }
}

private val Accent: Color = com.tabigabor.carweights.ui.theme.Accent

@Composable
private fun MakePickerSheet(
    allMakes: List<String>,
    selected: Set<String>,
    onApply: (Set<String>) -> Unit,
    onClear: () -> Unit,
) {
    var picked by remember(selected) { mutableStateOf(selected) }
    var q by remember { mutableStateOf("") }
    val filtered = remember(allMakes, q) {
        if (q.isBlank()) allMakes
        else allMakes.filter { it.contains(q, ignoreCase = true) }
    }
    Column(Modifier.padding(16.dp).fillMaxWidth()) {
        Text("Make filter", fontWeight = FontWeight.Bold, color = Text, fontSize = 18.sp)
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = q,
            onValueChange = { q = it },
            placeholder = { Text("Search makes…") },
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("${picked.size} selected · ${allMakes.size} total",
                color = Muted, fontSize = 12.sp)
            Spacer(Modifier.weight(1f))
            TextButton(onClick = { picked = emptySet() }) { Text("Clear") }
            TextButton(onClick = { picked = allMakes.toSet() }) { Text("All") }
        }
        Spacer(Modifier.height(4.dp))
        LazyColumn(modifier = Modifier.height(420.dp)) {
            items(filtered) { m ->
                val on = m in picked
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    androidx.compose.material3.Checkbox(
                        checked = on,
                        onCheckedChange = { checked ->
                            picked = if (checked) picked + m else picked - m
                        },
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(m, color = Text, fontSize = 14.sp)
                }
            }
        }
        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            TextButton(onClick = onClear) { Text("Reset") }
            Spacer(Modifier.width(8.dp))
            TextButton(onClick = { onApply(picked) }) {
                Text("Apply", fontWeight = FontWeight.Bold)
            }
        }
        Spacer(Modifier.height(8.dp))
    }
}

@Composable
private fun ThresholdCard(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    color: Color,
    value: Int,
    onChange: (Int) -> Unit,
) {
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Column(Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(8.dp))
                Text(title, fontWeight = FontWeight.SemiBold, color = Text, fontSize = 15.sp)
                Spacer(Modifier.weight(1f))
                Text(
                    "$value kg",
                    fontWeight = FontWeight.Bold,
                    color = color,
                    fontSize = 20.sp,
                )
            }
            Spacer(Modifier.height(6.dp))
            Slider(
                value = value.toFloat(),
                onValueChange = { onChange(((it / STEP).toInt()) * STEP) },
                valueRange = MIN_THR.toFloat()..MAX_THR.toFloat(),
                steps = ((MAX_THR - MIN_THR) / STEP) - 1,
                colors = SliderDefaults.colors(
                    thumbColor = color,
                    activeTrackColor = color,
                ),
            )
            Row {
                Text("$MIN_THR", style = MaterialTheme.typography.labelSmall, color = Muted)
                Spacer(Modifier.weight(1f))
                Text("$MAX_THR", style = MaterialTheme.typography.labelSmall, color = Muted)
            }
        }
    }
}

@Composable
private fun DistributionCard(o: PolicyOutcome, total: Int) {
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Column(Modifier.padding(14.dp)) {
            Text("Fleet outcome · ${o.total.locs()} of ${total.locs()} cars",
                fontWeight = FontWeight.SemiBold, color = Text, fontSize = 15.sp)
            Spacer(Modifier.height(10.dp))
            DistributionBar(o)
            Spacer(Modifier.height(10.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Legend("OK", o.countOk, o.pctOk, Green)
                Legend("Double", o.countDouble, o.pctDouble, Red)
                Legend("Borderline", o.countBorderline, o.pctBorderline, Amber)
                Legend("Unknown", o.countUnknown, o.pctUnknown, Grey)
            }
        }
    }
}

@Composable
private fun DistributionBar(o: PolicyOutcome) {
    Row(
        Modifier
            .fillMaxWidth()
            .height(20.dp)
            .clip(RoundedCornerShape(10.dp))
    ) {
        BarSegment(o.pctOk, Green)
        BarSegment(o.pctDouble, Red)
        BarSegment(o.pctBorderline, Amber)
        BarSegment(o.pctUnknown, Grey)
    }
}

@Composable
private fun androidx.compose.foundation.layout.RowScope.BarSegment(pct: Double, color: Color) {
    if (pct > 0) {
        Box(
            Modifier
                .weight(pct.toFloat())
                .fillMaxSize()
                .background(color)
        )
    }
}

@Composable
private fun Legend(label: String, n: Int, pct: Double, color: Color) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(10.dp).clip(RoundedCornerShape(5.dp)).background(color))
            Spacer(Modifier.width(6.dp))
            Text(label, color = Text, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
        }
        Spacer(Modifier.height(2.dp))
        Text("${n.locs()}  ·  ${"%.1f".format(pct)}%",
            color = Muted, fontSize = 11.sp)
    }
}

@Composable
private fun BorderCasesCard(
    outcome: PolicyOutcome,
    onOpenCar: (Long) -> Unit,
) {
    val cases5 = outcome.borderCases(5.0)
    val cases10 = outcome.borderCases(10.0)
    val cases25 = outcome.borderCases(25.0)
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Column(Modifier.padding(14.dp)) {
            Text("Border cases — cars paying double within…",
                fontWeight = FontWeight.SemiBold, color = Text, fontSize = 15.sp)
            Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Bucket("≤ 5%", cases5, Red)
                Bucket("≤ 10%", cases10, Amber)
                Bucket("≤ 25%", cases25, Muted)
            }
            Spacer(Modifier.height(10.dp))
            if (cases25.isEmpty()) {
                Text("No border cases at this policy.", color = Muted, fontSize = 12.sp)
            } else {
                Text(
                    "Closest to threshold (tap for details):",
                    color = Muted, fontSize = 11.sp,
                )
                Spacer(Modifier.height(4.dp))
                cases25.take(10).forEach { d ->
                    BorderRow(d, onClick = { onOpenCar(d.car.id) })
                }
                if (cases25.size > 10) {
                    Text(
                        "+ ${cases25.size - 10} more",
                        color = Muted, fontSize = 11.sp,
                        modifier = Modifier.padding(start = 8.dp, top = 4.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun Bucket(label: String, items: List<CarDecision>, color: Color) {
    Column {
        Text(label, color = color, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
        Text(items.size.locs(),
            color = Text, fontSize = 20.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun BorderRow(d: CarDecision, onClick: () -> Unit) {
    val c = d.car
    val w = d.repsWeight ?: 0
    val pctOver = d.marginPct ?: 0.0
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(Panel2)
            .padding(horizontal = 8.dp, vertical = 6.dp)
            .clickable { onClick() }
            .padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                "${c.make} ${c.model}${c.trim?.let { " $it" } ?: ""}",
                color = Text, fontSize = 13.sp, maxLines = 1,
            )
            Text(
                "${c.powertrainSubtype ?: c.powertrainType} · ${d.threshold} kg",
                color = Muted, fontSize = 11.sp,
            )
        }
        Text(
            "$w kg  +${"%.1f".format(pctOver)}%",
            color = Red, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun LoadingCard() {
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Column(Modifier.padding(14.dp)) {
            Text("Loading fleet…", fontWeight = FontWeight.SemiBold, color = Text)
            Spacer(Modifier.height(4.dp))
            Text("Reading the bundled cars.db (9k+ rows).",
                color = Muted, fontSize = 12.sp)
        }
    }
}

@Composable
private fun ErrorCard(msg: String) {
    Card(colors = CardDefaults.cardColors(containerColor = Panel)) {
        Column(Modifier.padding(14.dp)) {
            Text("Could not load the fleet", fontWeight = FontWeight.SemiBold, color = Red)
            Spacer(Modifier.height(4.dp))
            Text(msg, color = Muted, fontSize = 12.sp)
        }
    }
}

@Composable
private fun NoteCard(policy: Policy) {
    Card(colors = CardDefaults.cardColors(containerColor = Panel2)) {
        Column(Modifier.padding(12.dp)) {
            Text(
                "Default 2027 rule: BEV > ${FeeClassifier.THRESHOLD_BEV} kg, ICE/PHEV > ${FeeClassifier.THRESHOLD_COMBUSTION} kg.",
                color = Muted, fontSize = 11.sp,
            )
            Text(
                "Currently: BEV ${policy.bevThresholdKg} kg · ICE ${policy.combustionThresholdKg} kg.",
                color = Muted, fontSize = 11.sp,
            )
        }
    }
}
