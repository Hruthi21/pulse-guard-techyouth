// HealthReader.kt — reads today's data from Health Connect
package com.pulseguard.sync

import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.records.*
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import java.time.LocalDate
import java.time.ZoneId

data class DayHealth(
    val date:      String,
    val steps:     Long,
    val calories:  Double?,
    val heartRate: Double?,
    val restingHr: Double?,
    val distanceM: Double?,
)

object HealthReader {

    suspend fun readToday(client: HealthConnectClient): DayHealth {
        val today   = LocalDate.now()
        val start   = today.atStartOfDay(ZoneId.systemDefault()).toInstant()
        val end     = today.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant()
        val filter  = TimeRangeFilter.between(start, end)

        // Steps
        val stepsResp = client.readRecords(ReadRecordsRequest(StepsRecord::class, filter))
        val totalSteps = stepsResp.records.sumOf { it.count }

        // Calories
        val calResp = client.readRecords(ReadRecordsRequest(TotalCaloriesBurnedRecord::class, filter))
        val totalCal = calResp.records.sumOf { it.energy.inKilocalories }.takeIf { it > 0 }

        // Heart rate (average bpm)
        val hrResp = client.readRecords(ReadRecordsRequest(HeartRateRecord::class, filter))
        val allBpm = hrResp.records.flatMap { it.samples }.map { it.beatsPerMinute.toDouble() }
        val avgHr  = if (allBpm.isNotEmpty()) allBpm.average() else null

        // Resting HR
        val rhrResp = client.readRecords(ReadRecordsRequest(RestingHeartRateRecord::class, filter))
        val latestRhr = rhrResp.records.lastOrNull()?.beatsPerMinute?.toDouble()

        // Distance
        val distResp = client.readRecords(ReadRecordsRequest(DistanceRecord::class, filter))
        val totalDist = distResp.records.sumOf { it.distance.inMeters }.takeIf { it > 0 }

        return DayHealth(
            date      = today.toString(),
            steps     = totalSteps,
            calories  = totalCal,
            heartRate = avgHr?.let { Math.round(it * 10) / 10.0 },
            restingHr = latestRhr,
            distanceM = totalDist?.let { Math.round(it * 10) / 10.0 },
        )
    }
}
