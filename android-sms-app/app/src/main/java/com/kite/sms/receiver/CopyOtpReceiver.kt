package com.kite.sms.receiver

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.widget.Toast

/**
 * Handles the "Copy" action from OTP notifications.
 * Copies the OTP code to clipboard and dismisses the notification.
 */
class CopyOtpReceiver : BroadcastReceiver() {

    companion object {
        const val ACTION_COPY_OTP = "com.kite.sms.COPY_OTP"
        const val EXTRA_OTP_CODE = "otp_code"
        const val EXTRA_NOTIFICATION_ID = "notification_id"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION_COPY_OTP) return

        val otp = intent.getStringExtra(EXTRA_OTP_CODE) ?: return
        val notificationId = intent.getIntExtra(EXTRA_NOTIFICATION_ID, 0)

        // Copy to clipboard
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("OTP", otp))

        // Dismiss notification
        val nm = context.getSystemService(NotificationManager::class.java)
        nm.cancel(notificationId)

        // Toast confirmation (Android 12 and below - 13+ shows clipboard preview automatically)
        if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.TIRAMISU) {
            Toast.makeText(context, "OTP copied: $otp", Toast.LENGTH_SHORT).show()
        }
    }
}
