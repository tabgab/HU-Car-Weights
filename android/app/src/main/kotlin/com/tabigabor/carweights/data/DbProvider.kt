package com.tabigabor.carweights.data

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import java.io.File
import java.io.FileOutputStream

/**
 * Provides read-only access to the bundled cars.db (mirrors app/db.py).
 *
 * - First launch: decompresses the asset from APK into filesDir/cars.db (no-op here; gz
 *   decompression is handled in DbBootstrapper if a .gz asset is used).
 * - Subsequent launches: opens the existing file read-only.
 *
 * The bundled DB ships as plain `cars.db` (not gz) inside the APK assets for now —
 * tradeoff: ~7MB vs. ~16MB uncompressed. The repo also has `backups/cars.db.gz`
 * (~2.4MB); if size matters we add a decompress step later.
 */
object DbProvider {
    private const val DB_NAME = "cars.db"

    @Volatile private var cached: SQLiteDatabase? = null

    @Synchronized
    fun open(context: Context): SQLiteDatabase {
        cached?.let { return it }
        val dbFile = File(context.filesDir, DB_NAME)
        if (!dbFile.exists()) {
            copyFromAssets(context, dbFile)
        }
        val db = SQLiteDatabase.openDatabase(
            dbFile.absolutePath, null,
            SQLiteDatabase.OPEN_READONLY
        )
        cached = db
        return db
    }

    private fun copyFromAssets(context: Context, target: File) {
        context.assets.open(DB_NAME).use { input ->
            FileOutputStream(target).use { out -> input.copyTo(out) }
        }
    }
}
