package com.kite.sms.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * BroadcastReceiver for incoming MMS messages.
 * Required for default SMS app registration, even if MMS handling is basic.
 */
class MmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        // MMS handling - required for default SMS app capability
        // Full MMS support can be implemented here in the future
    }
}
