package com.tabigabor.carweights

import android.app.Application
import androidx.multidex.MultiDex

class CarWeightsApp : Application() {
    lateinit var state: AppState
        private set

    override fun onCreate() {
        super.onCreate()
        MultiDex.install(this)
        state = AppState(this)
    }
}
