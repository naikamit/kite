package com.kite.sms.model

/**
 * Represents a single SMS message.
 */
data class Message(
    val id: Long,
    val threadId: Long,
    val address: String,
    val body: String,
    val timestamp: Long,
    val type: MessageType,
    val isRead: Boolean,
    val status: DeliveryStatus = DeliveryStatus.NONE
) {
    val formattedTime: String
        get() {
            val sdf = java.text.SimpleDateFormat("h:mm a", java.util.Locale.getDefault())
            return sdf.format(java.util.Date(timestamp))
        }

    val formattedDate: String
        get() {
            val now = System.currentTimeMillis()
            val diff = now - timestamp
            val days = diff / (1000 * 60 * 60 * 24)

            return when {
                days < 1 -> "Today"
                days < 2 -> "Yesterday"
                days < 7 -> {
                    val sdf = java.text.SimpleDateFormat("EEEE", java.util.Locale.getDefault())
                    sdf.format(java.util.Date(timestamp))
                }
                else -> {
                    val sdf = java.text.SimpleDateFormat("MMMM d, yyyy", java.util.Locale.getDefault())
                    sdf.format(java.util.Date(timestamp))
                }
            }
        }

    val isSent: Boolean
        get() = type == MessageType.SENT

    val isReceived: Boolean
        get() = type == MessageType.RECEIVED
}

enum class MessageType(val value: Int) {
    RECEIVED(1),
    SENT(2),
    DRAFT(3),
    OUTBOX(4),
    FAILED(5),
    QUEUED(6);

    companion object {
        fun fromValue(value: Int): MessageType {
            return entries.find { it.value == value } ?: RECEIVED
        }
    }
}

enum class DeliveryStatus {
    NONE,
    PENDING,
    DELIVERED,
    FAILED
}
