// MainActivity.kt
package com.pulseguard.sync

import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Bundle
import android.widget.*
import androidx.activity.result.ActivityResultLauncher
import androidx.appcompat.app.AppCompatActivity
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.*
import androidx.lifecycle.lifecycleScope
import androidx.work.*
import kotlinx.coroutines.launch
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var prefs: SharedPreferences
    private var client: HealthConnectClient? = null
    private lateinit var permLauncher: ActivityResultLauncher<Set<String>>

    // ── Views ──────────────────────────────────────────────────────────────
    private lateinit var tvStatus:       TextView
    private lateinit var tvSteps:        TextView
    private lateinit var etServerUrl:    EditText
    private lateinit var etPairingCode:  EditText
    private lateinit var btnSave:        Button
    private lateinit var btnPermissions: Button
    private lateinit var btnSyncNow:     Button

    private val PERMISSIONS = setOf(
        HealthPermission.getReadPermission(StepsRecord::class),
        HealthPermission.getReadPermission(HeartRateRecord::class),
        HealthPermission.getReadPermission(RestingHeartRateRecord::class),
        HealthPermission.getReadPermission(TotalCaloriesBurnedRecord::class),
        HealthPermission.getReadPermission(DistanceRecord::class),
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Register permission launcher unconditionally before any checks
        permLauncher = registerForActivityResult(
            PermissionController.createRequestPermissionResultContract()
        ) { granted ->
            val all = PERMISSIONS.all { it in granted }
            tvStatus.text = if (all) "All permissions granted — ready to sync!"
                            else "Some permissions denied. Tap Allow again."
            refreshStepsDisplay()
        }

        prefs          = getSharedPreferences("pulseguard", MODE_PRIVATE)
        tvStatus       = findViewById(R.id.tvStatus)
        tvSteps        = findViewById(R.id.tvSteps)
        etServerUrl    = findViewById(R.id.etServerUrl)
        etPairingCode  = findViewById(R.id.etPairingCode)
        btnSave        = findViewById(R.id.btnSave)
        btnPermissions = findViewById(R.id.btnPermissions)
        btnSyncNow     = findViewById(R.id.btnSyncNow)

        // Restore saved config with auto-default to current server IP
        etServerUrl.setText(prefs.getString("server_url", "http://172.17.19.193:5000"))
        etPairingCode.setText(prefs.getString("pairing_code", ""))

        // Health Connect client check with graceful fallback
        try {
            val sdkStatus = HealthConnectClient.getSdkStatus(this)
            if (sdkStatus == HealthConnectClient.SDK_AVAILABLE) {
                client = HealthConnectClient.getOrCreate(this)
                tvStatus.text = "Health Connect ready. Please pair and sync."
            } else if (sdkStatus == HealthConnectClient.SDK_UNAVAILABLE_PROVIDER_UPDATE_REQUIRED) {
                tvStatus.text = "Health Connect requires update from Google Play Store."
            } else {
                tvStatus.text = "Health Connect not installed. Please install from Play Store."
            }
        } catch (e: Throwable) {
            tvStatus.text = "Health Connect status: ${e.message}"
        }

        btnSave.setOnClickListener {
            val url  = etServerUrl.text.toString().trimEnd('/')
            val code = etPairingCode.text.toString().trim().uppercase()
            if (url.isBlank() || code.isBlank()) {
                Toast.makeText(this, "Please enter both Server URL and Pairing Code", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            prefs.edit().putString("server_url", url).putString("pairing_code", code).apply()
            tvStatus.text = "Pairing with $url..."
            lifecycleScope.launch {
                val res = Uploader.pair(url, code, android.os.Build.MODEL)
                tvStatus.text = res.message
            }
        }

        btnPermissions.setOnClickListener {
            val hc = client
            if (hc == null) {
                Toast.makeText(this, "Health Connect is not available on this device", Toast.LENGTH_LONG).show()
                try {
                    val uri = Uri.parse("market://details?id=com.google.android.apps.healthdata")
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                } catch (_: Exception) {}
                return@setOnClickListener
            }
            lifecycleScope.launch {
                try {
                    val granted = hc.permissionController.getGrantedPermissions()
                    if (PERMISSIONS.all { it in granted }) {
                        tvStatus.text = "All Health Connect permissions already granted."
                    } else {
                        permLauncher.launch(PERMISSIONS)
                    }
                } catch (e: Exception) {
                    tvStatus.text = "Permission error: ${e.message}"
                }
            }
        }

        btnSyncNow.setOnClickListener { triggerSync() }

        // Schedule periodic background sync
        schedulePeriodicSync()
        // Show today's steps if available
        refreshStepsDisplay()
    }

    private fun triggerSync() {
        val hc = client
        if (hc == null) {
            Toast.makeText(this, "Health Connect is not available. Please install it first.", Toast.LENGTH_SHORT).show()
            return
        }
        val req = OneTimeWorkRequestBuilder<SyncWorker>().build()
        WorkManager.getInstance(this).enqueue(req)
        tvStatus.text = "Sync triggered — checking server in a few seconds."
        refreshStepsDisplay()
    }

    private fun schedulePeriodicSync() {
        try {
            val req = PeriodicWorkRequestBuilder<SyncWorker>(30, TimeUnit.MINUTES)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .build()
            WorkManager.getInstance(this).enqueueUniquePeriodicWork(
                "pulseguard_sync",
                ExistingPeriodicWorkPolicy.KEEP,
                req
            )
        } catch (_: Exception) {}
    }

    private fun refreshStepsDisplay() {
        val hc = client ?: return
        lifecycleScope.launch {
            try {
                val today = HealthReader.readToday(hc)
                tvSteps.text = "Today: ${today.steps} steps"
            } catch (e: Exception) {
                tvSteps.text = "Grant permissions to see steps"
            }
        }
    }
}
