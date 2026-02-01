package com.kite.sms.service

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.telephony.TelephonyManager

/**
 * Headless service required for default SMS app registration.
 * Handles "respond via message" actions (e.g., quick reply when declining a call).
 */
class HeadlessSmsService : Service() {

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent != null) {
            val action = intent.action
            if (TelephonyManager.ACTION_RESPOND_VIA_MESSAGE == action) {
                // Handle respond-via-message intent
                // This is triggered when user selects "respond with message" during an incoming call
                val uri = intent.data
                val message = intent.getStringExtra(Intent.EXTRA_TEXT)

                if (uri != null && message != null) {
                    val address = uri.schemeSpecificPart
                    // Send the quick reply
                    com.kite.sms.util.SmsHelper.sendSms(this, address, message)
                }
            }
        }

        stopSelf(startId)
        return START_NOT_STICKY
    }
}
