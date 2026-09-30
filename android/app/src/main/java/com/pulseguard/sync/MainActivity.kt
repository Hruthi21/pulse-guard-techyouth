// MainActivity.kt
package com.pulseguard.sync

import android.content.SharedPreferences
import android.os.Bundle
import android.widget.*
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.*
import androidx.lifecycle.lifecycleScope
import androidx.work.*
import kotlinx.coroutines.launch
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var prefs: SharedPreferences
    private lateinit var client: HealthConnectClient
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

        prefs          = getSharedPreferences("pulseguard", MODE_PRIVATE)
        tvStatus       = findViewById(R.id.tvStatus)
        tvSteps        = findViewById(R.id.tvSteps)
        etServerUrl    = findViewById(R.id.etServerUrl)
        etPairingCode  = findViewById(R.id.etPairingCode)
        btnSave        = findViewById(R.id.btnSave)
        btnPermissions = findViewById(R.id.btnPermissions)
        btnSyncNow     = findViewById(R.id.btnSyncNow)

        // Restore saved config
        etServerUrl.setText(prefs.getString("server_url", ""))
        etPairingCode.setText(prefs.getString("pairing_code", ""))

        // Health Connect client
        if (HealthConnectClient.getSdkStatus(this) == HealthConnectClient.SDK_AVAILABLE) {
            client = HealthConnectClient.getOrCreate(this)
        } else {
            tvStatus.text = "Health Connect not available on this device."
            return
        }

        // Permission launcher using Health Connect contract
        permLauncher = registerForActivityResult(
            androidx.health.connect.client.PermissionController.createRequestPermissionResultContract()
        ) { granted ->
            val all = PERMISSIONS.all { it in granted }
            tvStatus.text = if (all) "All permissions granted — ready to sync!"
                            else "Some permissions denied. Tap Allow again."
        }

        btnSave.setOnClickListener {
            val url  = etServerUrl.text.toString().trimEnd('/')
            val code = etPairingCode.text.toString().trim().uppercase()
            prefs.edit().putString("server_url", url).putString("pairing_code", code).apply()
            // Send pairing request to server
            lifecycleScope.launch {
                val ok = Uploader.pair(url, code, android.os.Build.MODEL)
                tvStatus.text = if (ok) "Paired successfully with PulseGuard server!"
                                else "Pairing failed — check URL and code."
            }
        }

        btnPermissions.setOnClickListener {
            lifecycleScope.launch {
                val granted = client.permissionController.getGrantedPermissions()
                if (PERMISSIONS.all { it in granted }) {
                    tvStatus.text = "All Health Connect permissions already granted."
                } else {
                    permLauncher.launch(PERMISSIONS)
                }
            }
        }

        btnSyncNow.setOnClickListener { triggerSync() }

        // Schedule periodic background sync every 30 minutes
        schedulePeriodicSync()
        // Show today's steps if available
        refreshStepsDisplay()
    }

    private fun triggerSync() {
        val req = OneTimeWorkRequestBuilder<SyncWorker>().build()
        WorkManager.getInstance(this).enqueue(req)
        tvStatus.text = "Sync triggered — check server in a few seconds."
    }

    private fun schedulePeriodicSync() {
        val req = PeriodicWorkRequestBuilder<SyncWorker>(30, TimeUnit.MINUTES)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "pulseguard_sync",
            ExistingPeriodicWorkPolicy.KEEP,
            req
        )
    }

    private fun refreshStepsDisplay() {
        lifecycleScope.launch {
            try {
                val today = HealthReader.readToday(client)
                tvSteps.text = "Today: ${today.steps} steps"
            } catch (e: Exception) {
                tvSteps.text = "Grant permissions to see steps"
            }
        }
    }
}
