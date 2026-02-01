package com.kite.sms.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import com.kite.sms.util.ContactHelper
import com.kite.sms.util.NotificationHelper

/**
 * BroadcastReceiver for incoming SMS messages.
 * Handles SMS_RECEIVED broadcasts and shows notifications.
 */
class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages.isNullOrEmpty()) return

        // Group messages by sender (multi-part messages come as separate SmsMessage objects)
        val messageMap = mutableMapOf<String, StringBuilder>()
        var timestamp = System.currentTimeMillis()

        for (sms in messages) {
            val sender = sms.displayOriginatingAddress ?: sms.originatingAddress ?: continue
            messageMap.getOrPut(sender) { StringBuilder() }.append(sms.messageBody ?: "")
            timestamp = sms.timestampMillis
        }

        // Show notification for each sender
        for ((sender, body) in messageMap) {
            val contactName = ContactHelper.getContactName(context, sender) ?: sender

            // Get thread ID for this sender
            val threadId = getThreadId(context, sender)

            // Show notification
            NotificationHelper.showMessageNotification(
                context = context,
                threadId = threadId,
                senderName = contactName,
                senderAddress = sender,
                messageBody = body.toString()
            )
        }
    }

    /**
     * Get the thread ID for a given phone number by querying the SMS content provider.
     */
    private fun getThreadId(context: Context, address: String): Long {
        try {
            val cursor = context.contentResolver.query(
                Telephony.Sms.CONTENT_URI,
                arrayOf(Telephony.Sms.THREAD_ID),
                "${Telephony.Sms.ADDRESS} = ?",
                arrayOf(address),
                "${Telephony.Sms.DATE} DESC LIMIT 1"
            )

            cursor?.use {
                if (it.moveToFirst()) {
                    return it.getLong(it.getColumnIndexOrThrow(Telephony.Sms.THREAD_ID))
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // Return a hash-based ID if we can't find the thread
        return address.hashCode().toLong()
    }
}
