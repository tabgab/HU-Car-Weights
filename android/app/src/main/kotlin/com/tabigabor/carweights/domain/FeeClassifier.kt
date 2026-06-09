package com.tabigabor.carweights.domain

/**
 * Budapest parking-fee classification — single source of truth for the app.
 * Mirrors app/fees.py byte-for-byte (mirrored in tests).
 *
 * Rule (effective 2027-01-01):
 *   - BEV (fully electric) over 2000 kg  -> pays double
 *   - ICE or PHEV over 1800 kg           -> pays double
 * "over X" is strict (>). Exactly at the threshold is OK.
 */
object FeeClassifier {
    const val THRESHOLD_BEV: Int = 2000
    const val THRESHOLD_COMBUSTION: Int = 1800  // ICE and PHEV

    fun thresholdFor(powertrainType: String?): Int =
        if (powertrainType == "BEV") THRESHOLD_BEV else THRESHOLD_COMBUSTION

    /**
     * @return OK | DOUBLE | BORDERLINE | UNKNOWN
     */
    fun classify(
        powertrainType: String?,
        weight: Int?,
        weightMin: Int? = null,
        weightMax: Int? = null,
    ): FeeStatus {
        val t = thresholdFor(powertrainType)
        val lo = weightMin ?: weight
        val hi = weightMax ?: weight
        if (lo == null && hi == null) return FeeStatus.UNKNOWN
        if (lo != null && hi != null) {
            return when {
                lo > t -> FeeStatus.DOUBLE        // entire range above threshold
                hi <= t -> FeeStatus.OK          // entire range at/below threshold
                else -> FeeStatus.BORDERLINE     // range straddles threshold (lo <= t < hi)
            }
        }
        val rep = weight ?: lo ?: hi
        if (rep == null) return FeeStatus.UNKNOWN
        return if (rep > t) FeeStatus.DOUBLE else FeeStatus.OK
    }
}
