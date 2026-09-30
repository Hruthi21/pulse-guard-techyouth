// Uploader.kt — sends health data to the Flask server over HTTP
package com.pulseguard.sync

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

data class ApiResult(val ok: Boolean, val message: String)

object Uploader {

    /** Pair the app with the server using the pairing code from /connect-phone. */
    suspend fun pair(serverUrl: String, pairingCode: String, deviceName: String): ApiResult =
        withContext(Dispatchers.IO) {
            try {
                val payload = JSONObject().apply {
                    put("pairing_code", pairingCode)
                    put("device_name",  deviceName)
                }
                val code = post("$serverUrl/api/phone/pair", payload, pairingCode)
                if (code in 200..299) {
                    ApiResult(true, "Paired successfully with PulseGuard server!")
                } else {
                    ApiResult(false, "Server returned HTTP $code (Check Pairing Code).")
                }
            } catch (e: Exception) {
                ApiResult(false, "Connection error: ${e.localizedMessage ?: e.message}")
            }
        }

    /** Upload today's health data to Flask. Returns true on success. */
    suspend fun uploadDay(serverUrl: String, pairingCode: String, health: DayHealth): Boolean =
        withContext(Dispatchers.IO) {
            try {
                val payload = JSONObject().apply {
                    put("pairing_code", pairingCode)
                    put("date",         health.date)
                    put("steps",        health.steps)
                    health.calories?.let  { put("calories",   it) }
                    health.heartRate?.let { put("heart_rate", it) }
                    health.restingHr?.let { put("resting_hr", it) }
                    health.distanceM?.let { put("distance_m", it) }
                }
                val code = post("$serverUrl/api/phone/sync", payload, pairingCode)
                code in 200..299
            } catch (e: Exception) {
                false
            }
        }

    // ── Internal ─────────────────────────────────────────────────────────

    private fun post(urlStr: String, body: JSONObject, pairingCode: String): Int {
        val conn = URL(urlStr).openConnection() as HttpURLConnection
        return try {
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.setRequestProperty("X-Pairing-Code", pairingCode)
            conn.doOutput  = true
            conn.connectTimeout = 10_000
            conn.readTimeout    = 10_000
            OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
            conn.responseCode
        } finally {
            conn.disconnect()
        }
    }
}
