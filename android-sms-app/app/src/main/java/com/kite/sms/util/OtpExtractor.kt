package com.kite.sms.util

/**
 * Fast OTP extraction from Indian SMS messages.
 * Pre-compiled regexes, ordered by frequency in Indian banking/service SMS.
 * Returns the OTP string or null if the message is not an OTP.
 */
object OtpExtractor {

    // Indian OTP messages almost always contain one of these keywords near a digit sequence.
    // We check the keyword first (cheap string scan) before running any regex.
    private val OTP_KEYWORDS = arrayOf(
        "otp", "OTP",
        "one time password", "One Time Password", "ONE TIME PASSWORD",
        "verification code", "Verification Code",
        "verify", "Verify",
        "authenticate", "Authenticate",
        "CVD", "TOTP"
    )

    // Primary: captures 4-8 digit code that appears adjacent to an OTP keyword.
    // Covers:  "OTP is 123456", "OTP: 123456", "OTP - 123456", "123456 is your OTP"
    private val PATTERN_NEAR_KEYWORD = Regex(
        """(?:OTP|otp|One Time Password|one time password|verification code|Verification Code)[:\s\-is]+(\d{4,8})\b""" +
        """|""" +
        """\b(\d{4,8})\s+(?:is your|is the|as your|as the)\s+(?:OTP|otp|One Time Password|one time password|verification code)"""
    )

    // Fallback: any standalone 4-8 digit sequence in a message we already know contains an OTP keyword.
    private val PATTERN_DIGITS = Regex("""\b(\d{4,8})\b""")

    // Negative signals - messages that contain digits but are NOT OTPs.
    private val NEGATIVE_KEYWORDS = arrayOf(
        "credited", "debited", "balance", "statement",
        "EMI", "due", "reward", "offer", "cashback",
        "dispatched", "delivered", "shipped", "tracking"
    )

    data class OtpResult(val code: String, val sender: String, val fullMessage: String)

    /**
     * Returns the OTP code if this message is an OTP SMS, null otherwise.
     * Designed for minimal allocations on the hot path.
     */
    fun extract(messageBody: String): String? {
        // Fast keyword scan - bail early if no OTP keyword found
        var hasKeyword = false
        for (kw in OTP_KEYWORDS) {
            if (messageBody.contains(kw)) {
                hasKeyword = true
                break
            }
        }
        if (!hasKeyword) return null

        // Negative check - skip transactional/promo messages that happen to say "OTP"
        for (neg in NEGATIVE_KEYWORDS) {
            if (messageBody.contains(neg, ignoreCase = true)) return null
        }

        // Try primary pattern (keyword-adjacent digits)
        PATTERN_NEAR_KEYWORD.find(messageBody)?.let { match ->
            // One of the two capture groups will be non-null
            val code = match.groupValues[1].ifEmpty { match.groupValues[2] }
            if (code.isNotEmpty()) return code
        }

        // Fallback: first 4-8 digit sequence in the message
        PATTERN_DIGITS.find(messageBody)?.let { match ->
            return match.groupValues[1]
        }

        return null
    }
}
