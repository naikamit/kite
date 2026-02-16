package com.kite.sms.receiver

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import androidx.core.app.NotificationCompat
import com.kite.sms.R
import com.kite.sms.util.OtpExtractor

/**
 * BroadcastReceiver for incoming SMS.
 * Auto-copies OTP to clipboard and shows a notification for 10 seconds.
 */
class SmsReceiver : BroadcastReceiver() {

    companion object {
        private const val CHANNEL_ID = "otp_channel"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
        if (messages.isEmpty()) return

        // Reassemble multi-part SMS
        val body = StringBuilder()
        for (sms in messages) {
            body.append(sms.messageBody ?: "")
        }

        val otp = OtpExtractor.extract(body.toString()) ?: return

        // Copy to clipboard immediately
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("OTP", otp))

        // Show notification for 10 seconds
        showOtpNotification(context, otp)
    }

    private fun showOtpNotification(context: Context, otp: String) {
        val notificationManager = context.getSystemService(NotificationManager::class.java)

        // Create channel
        val channel = NotificationChannel(
            CHANNEL_ID,
            "OTP Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "OTP copy notifications"
            setShowBadge(false)
        }
        notificationManager.createNotificationChannel(channel)

        // Copy action
        val copyIntent = Intent(context, CopyOtpReceiver::class.java).apply {
            action = CopyOtpReceiver.ACTION_COPY_OTP
            putExtra(CopyOtpReceiver.EXTRA_OTP_CODE, otp)
            putExtra(CopyOtpReceiver.EXTRA_NOTIFICATION_ID, 1)
        }
        val copyPending = PendingIntent.getBroadcast(
            context, 1, copyIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_message)
            .setContentTitle("OTP copied: $otp")
            .setContentText("Tap to copy again")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setAutoCancel(true)
            .setTimeoutAfter(10000)  // Auto-dismiss after 10 seconds
            .setContentIntent(copyPending)
            .addAction(R.drawable.ic_copy, "Copy", copyPending)
            .build()

        notificationManager.notify(1, notification)
    }
}
