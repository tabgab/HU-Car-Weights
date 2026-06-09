package com.tabigabor.carweights

import android.app.Application
import com.tabigabor.carweights.data.CarsRepository

class CarWeightsApp : Application() {
    val repository: CarsRepository by lazy { CarsRepository(this) }
}
