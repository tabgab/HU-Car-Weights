package com.tabigabor.carweights.domain

/** A user-defined policy: per-powertrain weight threshold (kg). */
data class Policy(
    val bevThresholdKg: Int = FeeClassifier.THRESHOLD_BEV,
    val combustionThresholdKg: Int = FeeClassifier.THRESHOLD_COMBUSTION,
) {
    fun thresholdFor(powertrainType: String?): Int =
        if (powertrainType == "BEV") bevThresholdKg else combustionThresholdKg
}

/** Status distribution + total over the full fleet. */
data class PolicyOutcome(
    val policy: Policy,
    val decisions: List<CarDecision>,
) {
    val total: Int get() = decisions.size

    private val byStatus: Map<FeeStatus, Int> =
        decisions.groupingBy { it.feeStatus }.eachCount()

    val countOk: Int get() = byStatus[FeeStatus.OK] ?: 0
    val countDouble: Int get() = byStatus[FeeStatus.DOUBLE] ?: 0
    val countBorderline: Int get() = byStatus[FeeStatus.BORDERLINE] ?: 0
    val countUnknown: Int get() = byStatus[FeeStatus.UNKNOWN] ?: 0

    val pctOk: Double get() = pct(countOk)
    val pctDouble: Double get() = pct(countDouble)
    val pctBorderline: Double get() = pct(countBorderline)
    val pctUnknown: Double get() = pct(countUnknown)

    private fun pct(n: Int): Double = if (total == 0) 0.0 else 100.0 * n / total

    /** Cars that pay double (status DOUBLE) AND are within `pctOver` of the threshold (e.g. 5.0). */
    fun borderCases(pctOver: Double): List<CarDecision> =
        decisions
            .asSequence()
            .filter { it.feeStatus == FeeStatus.DOUBLE }
            .mapNotNull { d ->
                val w = d.repsWeight ?: return@mapNotNull null
                val t = d.threshold
                if (t == 0) return@mapNotNull null
                val overPct = (w - t).toDouble() / t * 100.0
                if (overPct in 0.0..pctOver) d to overPct else null
            }
            .sortedBy { it.second }
            .map { it.first }
            .toList()
}
