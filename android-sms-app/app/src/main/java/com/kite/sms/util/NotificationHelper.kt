package com.kite.sms.util

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.kite.sms.ConversationActivity
import com.kite.sms.R

/**
 * Helper for creating and managing SMS notifications.
 */
object NotificationHelper {

    private const val CHANNEL_ID = "sms_messages"
    private const val CHANNEL_NAME = "SMS Messages"
    private const val CHANNEL_DESCRIPTION = "Notifications for incoming SMS messages"

    /**
     * Create the notification channel (required for Android 8+).
     */
    fun createNotificationChannel(context: Context) {
        val channel = NotificationChannel(
            CHANNEL_ID,
            CHANNEL_NAME,
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = CHANNEL_DESCRIPTION
            enableLights(true)
            enableVibration(true)
            setShowBadge(true)
        }

        val notificationManager = context.getSystemService(NotificationManager::class.java)
        notificationManager.createNotificationChannel(channel)
    }

    /**
     * Show a notification for an incoming SMS.
     */
    fun showMessageNotification(
        context: Context,
        threadId: Long,
        senderName: String,
        senderAddress: String,
        messageBody: String
    ) {
        val intent = Intent(context, ConversationActivity::class.java).apply {
            putExtra(ConversationActivity.EXTRA_THREAD_ID, threadId)
            putExtra(ConversationActivity.EXTRA_ADDRESS, senderAddress)
            putExtra(ConversationActivity.EXTRA_DISPLAY_NAME, senderName)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            threadId.toInt(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_message)
            .setContentTitle(senderName)
            .setContentText(messageBody)
            .setStyle(NotificationCompat.BigTextStyle().bigText(messageBody))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .build()

        val notificationManager = context.getSystemService(NotificationManager::class.java)
        notificationManager.notify(threadId.toInt(), notification)
    }

    /**
     * Cancel a notification for a specific thread.
     */
    fun cancelNotification(context: Context, threadId: Long) {
        val notificationManager = context.getSystemService(NotificationManager::class.java)
        notificationManager.cancel(threadId.toInt())
    }

    /**
     * Cancel all notifications.
     */
    fun cancelAll(context: Context) {
        val notificationManager = context.getSystemService(NotificationManager::class.java)
        notificationManager.cancelAll()
    }
}
