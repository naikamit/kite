package com.kite.sms.receiver

import android.content.BroadcastReceiver
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.provider.Telephony
import android.widget.Toast
import com.kite.sms.util.OtpExtractor

/**
 * BroadcastReceiver for incoming SMS.
 * Auto-copies OTP to clipboard and shows a toast.
 */
class SmsReceiver : BroadcastReceiver() {

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

        // Copy to clipboard
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("OTP", otp))

        // Show toast (LENGTH_LONG = ~3.5 seconds, max possible)
        Handler(Looper.getMainLooper()).post {
            Toast.makeText(context, "OTP copied: $otp", Toast.LENGTH_LONG).show()
        }
    }
}
