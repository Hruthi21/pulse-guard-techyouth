// SyncWorker.kt — WorkManager worker that runs in the background
package com.pulseguard.sync

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

class SyncWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {

    override suspend fun doWork(): Result {
        val prefs      = applicationContext.getSharedPreferences("pulseguard", Context.MODE_PRIVATE)
        val serverUrl  = prefs.getString("server_url",  "") ?: ""
        val pairingCode= prefs.getString("pairing_code","") ?: ""

        if (serverUrl.isBlank() || pairingCode.isBlank()) return Result.failure()

        return try {
            val client = HealthConnectClient.getOrCreate(applicationContext)
            val health = HealthReader.readToday(client)
            val ok     = Uploader.uploadDay(serverUrl, pairingCode, health)
            if (ok) Result.success() else Result.retry()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
