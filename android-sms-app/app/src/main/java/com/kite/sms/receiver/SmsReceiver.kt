package com.kite.sms.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import com.kite.sms.util.NotificationHelper
import com.kite.sms.util.OtpExtractor

/**
 * BroadcastReceiver for incoming SMS.
 * Only fires a notification for OTP messages. Everything else is ignored.
 * Optimized for minimum latency: no contact lookup, no DB query, straight to notification.
 */
class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
        if (messages.isEmpty()) return

        // Reassemble multi-part SMS per sender
        val bodies = mutableMapOf<String, StringBuilder>()
        for (sms in messages) {
            val sender = sms.originatingAddress ?: continue
            bodies.getOrPut(sender) { StringBuilder() }.append(sms.messageBody ?: "")
        }

        for ((sender, body) in bodies) {
            val text = body.toString()
            val otp = OtpExtractor.extract(text) ?: continue

            // OTP found — fire notification immediately
            NotificationHelper.showOtpNotification(context, sender, otp, text)
        }
    }
}
