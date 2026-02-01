# Kite SMS - Native Android SMS App

A clean, native Android SMS application built with Kotlin and Material Design 3.

## Features

- **Conversation List** - All SMS threads displayed in a clean inbox view with contact avatars, message previews, and timestamps
- **Chat View** - Messages displayed in chat-bubble style (sent/received), grouped by date
- **Compose** - New message composition with contact search and autocomplete
- **Search** - Search across all conversations from the toolbar
- **Default SMS App** - Can be set as the device's default SMS handler
- **Notifications** - Incoming SMS notifications with quick-open to conversation
- **Contact Integration** - Resolves phone numbers to contact names and photos
- **Dark Mode** - Full dark theme support following system settings
- **Swipe to Refresh** - Pull down to refresh the conversation list
- **Multi-part SMS** - Handles long messages automatically
- **Delete** - Delete individual messages or entire conversations

## Architecture

```
com.kite.sms/
├── MainActivity.kt              # Conversation list (inbox)
├── ConversationActivity.kt      # Message thread view
├── ComposeActivity.kt           # New message composition
├── adapter/
│   ├── ConversationListAdapter.kt  # Inbox list adapter
│   ├── MessageAdapter.kt          # Chat messages adapter
│   └── ContactSearchAdapter.kt    # Contact autocomplete adapter
├── model/
│   ├── Conversation.kt         # Conversation thread model
│   └── Message.kt              # SMS message model
├── receiver/
│   ├── SmsReceiver.kt          # Incoming SMS broadcast receiver
│   └── MmsReceiver.kt          # MMS broadcast receiver (stub)
├── service/
│   └── HeadlessSmsService.kt   # Required for default SMS app
└── util/
    ├── SmsHelper.kt            # SMS read/write/send operations
    ├── ContactHelper.kt        # Contact name/photo resolution
    ├── PermissionHelper.kt     # Runtime permission management
    └── NotificationHelper.kt   # Notification channel and display
```

## Requirements

- Android Studio Hedgehog (2023.1.1) or later
- Android SDK 34 (Android 14)
- Minimum SDK: 26 (Android 8.0 Oreo)
- Kotlin 1.9.20
- JDK 17

## Build Instructions

### Using Android Studio

1. Open Android Studio
2. Select **File > Open** and navigate to the `android-sms-app` directory
3. Wait for Gradle sync to complete
4. Click **Run** or press `Shift+F10`

### Using Command Line

```bash
cd android-sms-app

# Build debug APK
./gradlew assembleDebug

# The APK will be at:
# app/build/outputs/apk/debug/app-debug.apk

# Install on connected device
./gradlew installDebug
```

## Permissions

The app requires the following permissions:

| Permission | Purpose |
|---|---|
| `READ_SMS` | Read existing SMS messages and conversations |
| `SEND_SMS` | Send new SMS messages |
| `RECEIVE_SMS` | Receive incoming SMS and show notifications |
| `READ_CONTACTS` | Display contact names and photos |
| `READ_PHONE_STATE` | Required for SMS functionality |
| `POST_NOTIFICATIONS` | Show notifications for new messages (Android 13+) |

## Setting as Default SMS App

On first launch, the app will prompt you to set it as the default SMS app. This is required for:
- Receiving SMS messages
- Writing to the SMS content provider
- Showing in the share menu for SMS

## Tech Stack

- **Language**: Kotlin
- **UI**: Material Design 3 (Material You)
- **Architecture**: Activity-based with coroutines for async operations
- **SMS Access**: Android Telephony content provider
- **Contact Resolution**: ContactsContract content provider
- **Async**: Kotlin Coroutines with lifecycleScope
- **Lists**: RecyclerView with ListAdapter and DiffUtil
- **Build**: Gradle 8.5 with AGP 8.2.0
