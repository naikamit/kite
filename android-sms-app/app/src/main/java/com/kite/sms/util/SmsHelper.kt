package com.kite.sms.util

import android.content.ContentResolver
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.provider.Telephony
import android.telephony.SmsManager
import com.kite.sms.model.Conversation
import com.kite.sms.model.Message
import com.kite.sms.model.MessageType

/**
 * Helper class for reading and sending SMS messages using the Android Telephony content provider.
 */
object SmsHelper {

    /**
     * Get all conversation threads from the SMS content provider.
     */
    fun getConversations(context: Context): List<Conversation> {
        val conversations = mutableListOf<Conversation>()
        val contentResolver = context.contentResolver
        val contactHelper = ContactHelper

        val projection = arrayOf(
            Telephony.Sms.Conversations.THREAD_ID,
            Telephony.Sms.Conversations.SNIPPET,
            Telephony.Sms.Conversations.MESSAGE_COUNT
        )

        val cursor: Cursor? = contentResolver.query(
            Telephony.Sms.Conversations.CONTENT_URI,
            projection,
            null,
            null,
            "date DESC"
        )

        cursor?.use {
            val threadIdIdx = it.getColumnIndexOrThrow(Telephony.Sms.Conversations.THREAD_ID)
            val snippetIdx = it.getColumnIndexOrThrow(Telephony.Sms.Conversations.SNIPPET)
            val countIdx = it.getColumnIndexOrThrow(Telephony.Sms.Conversations.MESSAGE_COUNT)

            while (it.moveToNext()) {
                val threadId = it.getLong(threadIdIdx)
                val snippet = it.getString(snippetIdx) ?: ""
                val messageCount = it.getInt(countIdx)

                // Get the latest message details for this thread
                val threadDetails = getThreadDetails(contentResolver, threadId)
                if (threadDetails != null) {
                    val address = threadDetails.first
                    val timestamp = threadDetails.second
                    val isRead = threadDetails.third

                    val displayName = contactHelper.getContactName(context, address) ?: address
                    val photoUri = contactHelper.getContactPhotoUri(context, address)

                    conversations.add(
                        Conversation(
                            threadId = threadId,
                            address = address,
                            displayName = displayName,
                            snippet = snippet,
                            timestamp = timestamp,
                            messageCount = messageCount,
                            isRead = isRead,
                            photoUri = photoUri
                        )
                    )
                }
            }
        }

        return conversations.sortedByDescending { it.timestamp }
    }

    /**
     * Get details of the latest message in a thread.
     */
    private fun getThreadDetails(
        contentResolver: ContentResolver,
        threadId: Long
    ): Triple<String, Long, Boolean>? {
        val projection = arrayOf(
            Telephony.Sms.ADDRESS,
            Telephony.Sms.DATE,
            Telephony.Sms.READ
        )

        val cursor = contentResolver.query(
            Telephony.Sms.CONTENT_URI,
            projection,
            "${Telephony.Sms.THREAD_ID} = ?",
            arrayOf(threadId.toString()),
            "${Telephony.Sms.DATE} DESC LIMIT 1"
        )

        cursor?.use {
            if (it.moveToFirst()) {
                val address = it.getString(it.getColumnIndexOrThrow(Telephony.Sms.ADDRESS)) ?: ""
                val date = it.getLong(it.getColumnIndexOrThrow(Telephony.Sms.DATE))
                val read = it.getInt(it.getColumnIndexOrThrow(Telephony.Sms.READ)) == 1
                return Triple(address, date, read)
            }
        }

        return null
    }

    /**
     * Get all messages in a conversation thread.
     */
    fun getMessages(context: Context, threadId: Long): List<Message> {
        val messages = mutableListOf<Message>()
        val contentResolver = context.contentResolver

        val projection = arrayOf(
            Telephony.Sms._ID,
            Telephony.Sms.THREAD_ID,
            Telephony.Sms.ADDRESS,
            Telephony.Sms.BODY,
            Telephony.Sms.DATE,
            Telephony.Sms.TYPE,
            Telephony.Sms.READ,
            Telephony.Sms.STATUS
        )

        val cursor = contentResolver.query(
            Telephony.Sms.CONTENT_URI,
            projection,
            "${Telephony.Sms.THREAD_ID} = ?",
            arrayOf(threadId.toString()),
            "${Telephony.Sms.DATE} ASC"
        )

        cursor?.use {
            val idIdx = it.getColumnIndexOrThrow(Telephony.Sms._ID)
            val threadIdx = it.getColumnIndexOrThrow(Telephony.Sms.THREAD_ID)
            val addressIdx = it.getColumnIndexOrThrow(Telephony.Sms.ADDRESS)
            val bodyIdx = it.getColumnIndexOrThrow(Telephony.Sms.BODY)
            val dateIdx = it.getColumnIndexOrThrow(Telephony.Sms.DATE)
            val typeIdx = it.getColumnIndexOrThrow(Telephony.Sms.TYPE)
            val readIdx = it.getColumnIndexOrThrow(Telephony.Sms.READ)

            while (it.moveToNext()) {
                messages.add(
                    Message(
                        id = it.getLong(idIdx),
                        threadId = it.getLong(threadIdx),
                        address = it.getString(addressIdx) ?: "",
                        body = it.getString(bodyIdx) ?: "",
                        timestamp = it.getLong(dateIdx),
                        type = MessageType.fromValue(it.getInt(typeIdx)),
                        isRead = it.getInt(readIdx) == 1
                    )
                )
            }
        }

        return messages
    }

    /**
     * Search messages across all conversations.
     */
    fun searchMessages(context: Context, query: String): List<Message> {
        val messages = mutableListOf<Message>()
        val contentResolver = context.contentResolver

        val projection = arrayOf(
            Telephony.Sms._ID,
            Telephony.Sms.THREAD_ID,
            Telephony.Sms.ADDRESS,
            Telephony.Sms.BODY,
            Telephony.Sms.DATE,
            Telephony.Sms.TYPE,
            Telephony.Sms.READ
        )

        val cursor = contentResolver.query(
            Telephony.Sms.CONTENT_URI,
            projection,
            "${Telephony.Sms.BODY} LIKE ?",
            arrayOf("%$query%"),
            "${Telephony.Sms.DATE} DESC LIMIT 50"
        )

        cursor?.use {
            val idIdx = it.getColumnIndexOrThrow(Telephony.Sms._ID)
            val threadIdx = it.getColumnIndexOrThrow(Telephony.Sms.THREAD_ID)
            val addressIdx = it.getColumnIndexOrThrow(Telephony.Sms.ADDRESS)
            val bodyIdx = it.getColumnIndexOrThrow(Telephony.Sms.BODY)
            val dateIdx = it.getColumnIndexOrThrow(Telephony.Sms.DATE)
            val typeIdx = it.getColumnIndexOrThrow(Telephony.Sms.TYPE)
            val readIdx = it.getColumnIndexOrThrow(Telephony.Sms.READ)

            while (it.moveToNext()) {
                messages.add(
                    Message(
                        id = it.getLong(idIdx),
                        threadId = it.getLong(threadIdx),
                        address = it.getString(addressIdx) ?: "",
                        body = it.getString(bodyIdx) ?: "",
                        timestamp = it.getLong(dateIdx),
                        type = MessageType.fromValue(it.getInt(typeIdx)),
                        isRead = it.getInt(readIdx) == 1
                    )
                )
            }
        }

        return messages
    }

    /**
     * Send an SMS message.
     */
    fun sendSms(context: Context, address: String, body: String): Boolean {
        return try {
            val smsManager = context.getSystemService(SmsManager::class.java)
            val parts = smsManager.divideMessage(body)

            if (parts.size == 1) {
                smsManager.sendTextMessage(address, null, body, null, null)
            } else {
                smsManager.sendMultipartTextMessage(address, null, parts, null, null)
            }

            // Save to sent messages
            saveSentMessage(context, address, body)
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    /**
     * Save a sent message to the SMS content provider.
     */
    private fun saveSentMessage(context: Context, address: String, body: String) {
        try {
            val values = android.content.ContentValues().apply {
                put(Telephony.Sms.ADDRESS, address)
                put(Telephony.Sms.BODY, body)
                put(Telephony.Sms.TYPE, Telephony.Sms.MESSAGE_TYPE_SENT)
                put(Telephony.Sms.DATE, System.currentTimeMillis())
                put(Telephony.Sms.READ, 1)
            }
            context.contentResolver.insert(Telephony.Sms.CONTENT_URI, values)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * Mark all messages in a thread as read.
     */
    fun markThreadAsRead(context: Context, threadId: Long) {
        try {
            val values = android.content.ContentValues().apply {
                put(Telephony.Sms.READ, 1)
            }
            context.contentResolver.update(
                Telephony.Sms.CONTENT_URI,
                values,
                "${Telephony.Sms.THREAD_ID} = ? AND ${Telephony.Sms.READ} = 0",
                arrayOf(threadId.toString())
            )
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * Delete a conversation thread.
     */
    fun deleteThread(context: Context, threadId: Long): Boolean {
        return try {
            val uri = Uri.parse("content://sms/conversations/$threadId")
            context.contentResolver.delete(uri, null, null)
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    /**
     * Delete a single message.
     */
    fun deleteMessage(context: Context, messageId: Long): Boolean {
        return try {
            val uri = Uri.parse("content://sms/$messageId")
            context.contentResolver.delete(uri, null, null) > 0
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    /**
     * Get the total count of unread messages.
     */
    fun getUnreadCount(context: Context): Int {
        val cursor = context.contentResolver.query(
            Telephony.Sms.CONTENT_URI,
            arrayOf("COUNT(*)"),
            "${Telephony.Sms.READ} = 0 AND ${Telephony.Sms.TYPE} = ${Telephony.Sms.MESSAGE_TYPE_INBOX}",
            null,
            null
        )

        cursor?.use {
            if (it.moveToFirst()) {
                return it.getInt(0)
            }
        }

        return 0
    }
}
