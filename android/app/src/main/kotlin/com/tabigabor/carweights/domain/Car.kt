package com.tabigabor.carweights.domain

data class Car(
    val id: Long,
    val make: String,
    val model: String,
    val trim: String?,
    val powertrainType: String,
    val powertrainSubtype: String?,
    val drivetrain: String?,
    val powerKw: Int?,
    val batteryKwh: Double?,
    val modelYear: Int?,
    val weight: Int?,
    val weightMin: Int?,
    val weightMax: Int?,
    val weightSource: String?,
    val huWeightKg: Int?,
    val sourcesAgree: Int?,
    val onSaleHu: Boolean,
)

enum class FeeStatus { OK, DOUBLE, BORDERLINE, UNKNOWN }

data class CarDecision(
    val car: Car,
    val threshold: Int,
    val feeStatus: FeeStatus,
) {
    val repsWeight: Int? get() = car.weight ?: car.weightMin ?: car.weightMax
    val marginKg: Int? get() = repsWeight?.let { it - threshold }
    val marginPct: Double? get() = repsWeight?.let { (it - threshold).toDouble() / threshold * 100.0 }
}
