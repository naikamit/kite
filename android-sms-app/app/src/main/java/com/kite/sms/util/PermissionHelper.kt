package com.kite.sms.util

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

/**
 * Helper for managing runtime permissions.
 */
object PermissionHelper {

    const val REQUEST_SMS_PERMISSIONS = 100
    const val REQUEST_CONTACTS_PERMISSION = 101
    const val REQUEST_NOTIFICATION_PERMISSION = 102

    /**
     * All SMS-related permissions needed.
     */
    val SMS_PERMISSIONS = arrayOf(
        Manifest.permission.READ_SMS,
        Manifest.permission.SEND_SMS,
        Manifest.permission.RECEIVE_SMS,
        Manifest.permission.READ_PHONE_STATE
    )

    val CONTACTS_PERMISSIONS = arrayOf(
        Manifest.permission.READ_CONTACTS
    )

    /**
     * Check if all SMS permissions are granted.
     */
    fun hasSmsPermissions(context: Context): Boolean {
        return SMS_PERMISSIONS.all {
            ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED
        }
    }

    /**
     * Check if contacts permission is granted.
     */
    fun hasContactsPermission(context: Context): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_CONTACTS
        ) == PackageManager.PERMISSION_GRANTED
    }

    /**
     * Check if notification permission is granted (Android 13+).
     */
    fun hasNotificationPermission(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    /**
     * Request all required permissions.
     */
    fun requestAllPermissions(activity: Activity) {
        val permissions = mutableListOf<String>()

        // SMS permissions
        SMS_PERMISSIONS.forEach {
            if (ContextCompat.checkSelfPermission(activity, it) != PackageManager.PERMISSION_GRANTED) {
                permissions.add(it)
            }
        }

        // Contacts permission
        if (!hasContactsPermission(activity)) {
            permissions.add(Manifest.permission.READ_CONTACTS)
        }

        // Notification permission (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (!hasNotificationPermission(activity)) {
                permissions.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        if (permissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                activity,
                permissions.toTypedArray(),
                REQUEST_SMS_PERMISSIONS
            )
        }
    }

    /**
     * Request SMS permissions only.
     */
    fun requestSmsPermissions(activity: Activity) {
        ActivityCompat.requestPermissions(activity, SMS_PERMISSIONS, REQUEST_SMS_PERMISSIONS)
    }

    /**
     * Request contacts permission only.
     */
    fun requestContactsPermission(activity: Activity) {
        ActivityCompat.requestPermissions(activity, CONTACTS_PERMISSIONS, REQUEST_CONTACTS_PERMISSION)
    }

    /**
     * Check if we should show permission rationale for any SMS permission.
     */
    fun shouldShowSmsRationale(activity: Activity): Boolean {
        return SMS_PERMISSIONS.any {
            ActivityCompat.shouldShowRequestPermissionRationale(activity, it)
        }
    }

    /**
     * Check if all permissions in the result were granted.
     */
    fun allPermissionsGranted(grantResults: IntArray): Boolean {
        return grantResults.isNotEmpty() && grantResults.all {
            it == PackageManager.PERMISSION_GRANTED
        }
    }
}
