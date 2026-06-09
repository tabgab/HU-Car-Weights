package com.tabigabor.carweights.data

import android.content.Context
import com.tabigabor.carweights.domain.Car

class CarsRepository(context: Context) {
    private val db = DbProvider.open(context)

    fun loadAll(): List<Car> {
        val sql = """
            SELECT id, make, model, trim, powertrain_type, powertrain_subtype, drivetrain,
                   power_kw, battery_kwh, model_year, weight, weight_min, weight_max,
                   weight_source, hu_weight_kg, sources_agree, on_sale_hu
            FROM v_parking_summary
            WHERE COALESCE(is_missing, 0) = 0
        """.trimIndent()
        return db.use {
            it.rawQuery(sql, null).use { c ->
                val out = ArrayList<Car>(c.count)
                while (c.moveToNext()) {
                    out.add(
                        Car(
                            id = c.getLong(0),
                            make = c.getString(1) ?: "",
                            model = c.getString(2) ?: "",
                            trim = c.getString(3),
                            powertrainType = c.getString(4) ?: "ICE",
                            powertrainSubtype = c.getString(5),
                            drivetrain = c.getString(6),
                            powerKw = c.getIntOrNull(7),
                            batteryKwh = c.getDoubleOrNull(8),
                            modelYear = c.getIntOrNull(9),
                            weight = c.getIntOrNull(10),
                            weightMin = c.getIntOrNull(11),
                            weightMax = c.getIntOrNull(12),
                            weightSource = c.getString(13),
                            huWeightKg = c.getIntOrNull(14),
                            sourcesAgree = c.getIntOrNull(15),
                            onSaleHu = (c.getIntOrNull(16) ?: 1) == 1,
                        )
                    )
                }
                out
            }
        }
    }
}

private fun android.database.Cursor.getIntOrNull(idx: Int): Int? =
    if (isNull(idx)) null else getInt(idx)

private fun android.database.Cursor.getDoubleOrNull(idx: Int): Double? =
    if (isNull(idx)) null else getDouble(idx)
