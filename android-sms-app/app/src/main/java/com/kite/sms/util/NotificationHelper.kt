package com.kite.sms.util

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.kite.sms.R
import com.kite.sms.receiver.CopyOtpReceiver

/**
 * OTP-only notification helper.
 * Shows a heads-up notification with the OTP code and a "Copy" action button.
 */
object NotificationHelper {

    private const val CHANNEL_ID = "otp_alerts"
    private const val CHANNEL_NAME = "OTP Alerts"

    /**
     * Create the notification channel. Call once from Application/Activity onCreate.
     */
    fun createNotificationChannel(context: Context) {
        val channel = NotificationChannel(
            CHANNEL_ID,
            CHANNEL_NAME,
            NotificationManager.IMPORTANCE_HIGH      // heads-up
        ).apply {
            description = "Instant OTP copy notifications"
            enableLights(true)
            enableVibration(true)
            setShowBadge(false)
            lockscreenVisibility = android.app.Notification.VISIBILITY_PUBLIC
        }

        context.getSystemService(NotificationManager::class.java)
            .createNotificationChannel(channel)
    }

    /**
     * Show an OTP notification with a Copy action button.
     * Designed for speed: no DB queries, no contact resolution, minimal object creation.
     */
    fun showOtpNotification(
        context: Context,
        sender: String,
        otpCode: String,
        fullMessage: String
    ) {
        val notificationId = (System.currentTimeMillis() % Int.MAX_VALUE).toInt()

        // Copy action intent
        val copyIntent = Intent(context, CopyOtpReceiver::class.java).apply {
            action = CopyOtpReceiver.ACTION_COPY_OTP
            putExtra(CopyOtpReceiver.EXTRA_OTP_CODE, otpCode)
            putExtra(CopyOtpReceiver.EXTRA_NOTIFICATION_ID, notificationId)
        }
        val copyPending = PendingIntent.getBroadcast(
            context,
            notificationId,
            copyIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_message)
            .setContentTitle("OTP: $otpCode")
            .setContentText("From $sender — tap Copy")
            .setSubText(sender)
            .setStyle(NotificationCompat.BigTextStyle().bigText(fullMessage))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setAutoCancel(true)
            .setContentIntent(copyPending)          // tap notification = copy
            .addAction(R.drawable.ic_copy, "Copy OTP", copyPending)
            .setDefaults(NotificationCompat.DEFAULT_SOUND or NotificationCompat.DEFAULT_VIBRATE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .build()

        context.getSystemService(NotificationManager::class.java)
            .notify(notificationId, notification)
    }
}
