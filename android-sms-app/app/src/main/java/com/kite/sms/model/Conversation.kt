package com.kite.sms.model

/**
 * Represents an SMS conversation thread.
 */
data class Conversation(
    val threadId: Long,
    val address: String,
    val displayName: String,
    val snippet: String,
    val timestamp: Long,
    val messageCount: Int,
    val isRead: Boolean,
    val photoUri: String? = null
) {
    val formattedTime: String
        get() {
            val now = System.currentTimeMillis()
            val diff = now - timestamp
            val seconds = diff / 1000
            val minutes = seconds / 60
            val hours = minutes / 60
            val days = hours / 24

            return when {
                minutes < 1 -> "Now"
                minutes < 60 -> "${minutes}m"
                hours < 24 -> "${hours}h"
                days < 7 -> "${days}d"
                else -> {
                    val sdf = java.text.SimpleDateFormat("MMM d", java.util.Locale.getDefault())
                    sdf.format(java.util.Date(timestamp))
                }
            }
        }

    val initials: String
        get() {
            val parts = displayName.trim().split("\\s+".toRegex())
            return when {
                parts.size >= 2 -> "${parts[0].first()}${parts[1].first()}".uppercase()
                parts.isNotEmpty() && parts[0].isNotEmpty() -> parts[0].first().uppercase().toString()
                else -> "#"
            }
        }
}
