package com.tabigabor.carweights

import android.content.Context
import android.content.SharedPreferences
import androidx.compose.runtime.mutableStateOf
import com.tabigabor.carweights.data.CarsRepository
import com.tabigabor.carweights.domain.Car
import kotlin.concurrent.thread

/**
 * Shared application state. Owned by the Application so it survives tab switches
 * and configuration changes. The cars list is loaded once, off the main thread.
 *
 * The text-size setting persists via SharedPreferences and feeds `LocalDensity` at the
 * Compose root, so sp-based text scales in lock-step with user choice.
 */
class AppState(context: Context) {
    val cars = mutableStateOf<List<Car>>(emptyList())
    val loadError = mutableStateOf<String?>(null)
    val isLoading = mutableStateOf(false)

    val fontScale = mutableStateOf(prefs(context).getFloat(KEY_FONT_SCALE, DEFAULT_FONT_SCALE))
    val huOnly = mutableStateOf(prefs(context).getBoolean(KEY_HU_ONLY, false))

    // Powertrain subtype filter for the Policy Explorer. Empty set = "All".
    // Values: BEV, PHEV, HEV, MHEV, petrol, diesel.
    val powertrainFilter = mutableStateOf<Set<String>>(
        prefs(context).getStringSet(KEY_PT_FILTER, emptySet()) ?: emptySet()
    )

    // Make filter for the Policy Explorer. Empty set = "All".
    val makeFilter = mutableStateOf<Set<String>>(
        prefs(context).getStringSet(KEY_MAKE_FILTER, emptySet()) ?: emptySet()
    )

    // Currently open car detail (null = none). Lifted here so any tab can open it.
    val selectedCarId = mutableStateOf<Long?>(null)

    init {
        reload(context)
    }

    fun reload(context: Context) {
        isLoading.value = true
        loadError.value = null
        thread(name = "cars-loader", isDaemon = true) {
            try {
                val list = CarsRepository(context).loadAll()
                cars.value = list
            } catch (t: Throwable) {
                loadError.value = t.message ?: t.javaClass.simpleName
            } finally {
                isLoading.value = false
            }
        }
    }

    fun setFontScale(context: Context, scale: Float) {
        fontScale.value = scale
        prefs(context).edit().putFloat(KEY_FONT_SCALE, scale).apply()
    }

    fun setHuOnly(context: Context, value: Boolean) {
        huOnly.value = value
        prefs(context).edit().putBoolean(KEY_HU_ONLY, value).apply()
    }

    fun setPowertrainFilter(context: Context, values: Set<String>) {
        powertrainFilter.value = values
        prefs(context).edit().putStringSet(KEY_PT_FILTER, values).apply()
    }

    fun setMakeFilter(context: Context, values: Set<String>) {
        makeFilter.value = values
        prefs(context).edit().putStringSet(KEY_MAKE_FILTER, values).apply()
    }

    companion object {
        const val PREFS = "carweights"
        const val KEY_FONT_SCALE = "font_scale"
        const val KEY_HU_ONLY = "hu_only"
        const val KEY_PT_FILTER = "pt_filter"
        const val KEY_MAKE_FILTER = "make_filter"
        const val DEFAULT_FONT_SCALE = 1.15f

        val FONT_SCALE_CHOICES = listOf(0.85f, 1.0f, 1.15f, 1.3f, 1.5f, 1.75f, 2.0f)

        /** Powertrain subtype options surfaced in the Policy filter UI. */
        val POWERTRAIN_FILTER_OPTIONS = listOf("BEV", "PHEV", "HEV", "MHEV", "petrol", "diesel")

        /** Top makes shown as quick chips before opening the full picker. */
        val TOP_MAKES = listOf(
            "Škoda", "Volkswagen", "BMW", "Audi", "Mercedes-Benz",
            "Toyota", "Hyundai", "Kia", "Ford", "Renault",
        )

        private fun prefs(context: Context): SharedPreferences =
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    }
}
