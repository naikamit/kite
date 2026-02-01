package com.kite.sms.util

import android.content.Context
import android.net.Uri
import android.provider.ContactsContract

/**
 * Helper for resolving phone numbers to contact names and photos.
 */
object ContactHelper {

    private val nameCache = mutableMapOf<String, String?>()
    private val photoCache = mutableMapOf<String, String?>()

    /**
     * Get the contact display name for a phone number.
     */
    fun getContactName(context: Context, phoneNumber: String): String? {
        if (phoneNumber.isBlank()) return null

        // Check cache first
        nameCache[phoneNumber]?.let { return it }

        val name = lookupContactName(context, phoneNumber)
        nameCache[phoneNumber] = name
        return name
    }

    /**
     * Get the contact photo URI for a phone number.
     */
    fun getContactPhotoUri(context: Context, phoneNumber: String): String? {
        if (phoneNumber.isBlank()) return null

        // Check cache first
        if (photoCache.containsKey(phoneNumber)) return photoCache[phoneNumber]

        val photoUri = lookupContactPhotoUri(context, phoneNumber)
        photoCache[phoneNumber] = photoUri
        return photoUri
    }

    /**
     * Look up contact name from the contacts content provider.
     */
    private fun lookupContactName(context: Context, phoneNumber: String): String? {
        try {
            val uri = Uri.withAppendedPath(
                ContactsContract.PhoneLookup.CONTENT_FILTER_URI,
                Uri.encode(phoneNumber)
            )

            val projection = arrayOf(ContactsContract.PhoneLookup.DISPLAY_NAME)

            context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    return cursor.getString(
                        cursor.getColumnIndexOrThrow(ContactsContract.PhoneLookup.DISPLAY_NAME)
                    )
                }
            }
        } catch (e: Exception) {
            // Permission denied or other error
        }

        return null
    }

    /**
     * Look up contact photo URI from the contacts content provider.
     */
    private fun lookupContactPhotoUri(context: Context, phoneNumber: String): String? {
        try {
            val uri = Uri.withAppendedPath(
                ContactsContract.PhoneLookup.CONTENT_FILTER_URI,
                Uri.encode(phoneNumber)
            )

            val projection = arrayOf(ContactsContract.PhoneLookup.PHOTO_THUMBNAIL_URI)

            context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    return cursor.getString(
                        cursor.getColumnIndexOrThrow(ContactsContract.PhoneLookup.PHOTO_THUMBNAIL_URI)
                    )
                }
            }
        } catch (e: Exception) {
            // Permission denied or other error
        }

        return null
    }

    /**
     * Search contacts by name or number.
     */
    fun searchContacts(context: Context, query: String): List<ContactResult> {
        val results = mutableListOf<ContactResult>()
        if (query.isBlank()) return results

        try {
            val uri = Uri.withAppendedPath(
                ContactsContract.CommonDataKinds.Phone.CONTENT_FILTER_URI,
                Uri.encode(query)
            )

            val projection = arrayOf(
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER,
                ContactsContract.CommonDataKinds.Phone.PHOTO_THUMBNAIL_URI
            )

            context.contentResolver.query(
                uri,
                projection,
                null,
                null,
                "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} ASC LIMIT 20"
            )?.use { cursor ->
                val nameIdx = cursor.getColumnIndexOrThrow(
                    ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
                )
                val numberIdx = cursor.getColumnIndexOrThrow(
                    ContactsContract.CommonDataKinds.Phone.NUMBER
                )
                val photoIdx = cursor.getColumnIndexOrThrow(
                    ContactsContract.CommonDataKinds.Phone.PHOTO_THUMBNAIL_URI
                )

                while (cursor.moveToNext()) {
                    results.add(
                        ContactResult(
                            name = cursor.getString(nameIdx) ?: "",
                            phoneNumber = cursor.getString(numberIdx) ?: "",
                            photoUri = cursor.getString(photoIdx)
                        )
                    )
                }
            }
        } catch (e: Exception) {
            // Permission denied or other error
        }

        return results.distinctBy { it.phoneNumber }
    }

    /**
     * Clear the contact caches.
     */
    fun clearCache() {
        nameCache.clear()
        photoCache.clear()
    }

    data class ContactResult(
        val name: String,
        val phoneNumber: String,
        val photoUri: String?
    ) {
        val initials: String
            get() {
                val parts = name.trim().split("\\s+".toRegex())
                return when {
                    parts.size >= 2 -> "${parts[0].first()}${parts[1].first()}".uppercase()
                    parts.isNotEmpty() && parts[0].isNotEmpty() -> parts[0].first().uppercase()
                        .toString()
                    else -> "#"
                }
            }
    }
}
