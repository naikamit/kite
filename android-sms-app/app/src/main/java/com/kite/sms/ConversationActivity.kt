package com.kite.sms

import android.content.ClipData
import android.content.ClipboardManager
import android.os.Bundle
import android.view.MenuItem
import android.widget.EditText
import android.widget.ImageButton
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.kite.sms.adapter.MessageAdapter
import com.kite.sms.model.Message
import com.kite.sms.util.SmsHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Activity showing messages within a single conversation thread.
 * Displays chat-bubble style messages and allows sending replies.
 */
class ConversationActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_THREAD_ID = "extra_thread_id"
        const val EXTRA_ADDRESS = "extra_address"
        const val EXTRA_DISPLAY_NAME = "extra_display_name"
    }

    private var threadId: Long = -1
    private var address: String = ""
    private var displayName: String = ""

    private lateinit var recyclerView: RecyclerView
    private lateinit var messageInput: EditText
    private lateinit var sendButton: ImageButton
    private lateinit var adapter: MessageAdapter
    private lateinit var layoutManager: LinearLayoutManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_conversation)

        threadId = intent.getLongExtra(EXTRA_THREAD_ID, -1)
        address = intent.getStringExtra(EXTRA_ADDRESS) ?: ""
        displayName = intent.getStringExtra(EXTRA_DISPLAY_NAME) ?: address

        if (threadId == -1L || address.isEmpty()) {
            finish()
            return
        }

        setupToolbar()
        setupViews()
        setupAdapter()
        loadMessages()

        // Mark thread as read
        lifecycleScope.launch(Dispatchers.IO) {
            SmsHelper.markThreadAsRead(this@ConversationActivity, threadId)
        }
    }

    override fun onResume() {
        super.onResume()
        loadMessages()
    }

    private fun setupToolbar() {
        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        setSupportActionBar(toolbar)
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            title = displayName
            subtitle = if (displayName != address) address else null
        }
    }

    private fun setupViews() {
        recyclerView = findViewById(R.id.recycler_messages)
        messageInput = findViewById(R.id.edit_message)
        sendButton = findViewById(R.id.button_send)

        sendButton.setOnClickListener {
            sendMessage()
        }

        // Enable send button only when there's text
        messageInput.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: android.text.Editable?) {
                sendButton.isEnabled = !s.isNullOrBlank()
                sendButton.alpha = if (s.isNullOrBlank()) 0.5f else 1.0f
            }
        })

        sendButton.isEnabled = false
        sendButton.alpha = 0.5f
    }

    private fun setupAdapter() {
        adapter = MessageAdapter(
            onMessageLongClick = { message ->
                showMessageOptions(message)
                true
            }
        )

        layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }

        recyclerView.layoutManager = layoutManager
        recyclerView.adapter = adapter
    }

    private fun loadMessages() {
        lifecycleScope.launch {
            val messages = withContext(Dispatchers.IO) {
                SmsHelper.getMessages(this@ConversationActivity, threadId)
            }

            adapter.submitMessages(messages)

            // Scroll to bottom
            recyclerView.post {
                if (adapter.itemCount > 0) {
                    recyclerView.scrollToPosition(adapter.itemCount - 1)
                }
            }
        }
    }

    private fun sendMessage() {
        val body = messageInput.text.toString().trim()
        if (body.isEmpty()) return

        messageInput.text.clear()
        sendButton.isEnabled = false

        lifecycleScope.launch {
            val success = withContext(Dispatchers.IO) {
                SmsHelper.sendSms(this@ConversationActivity, address, body)
            }

            if (success) {
                loadMessages()
            } else {
                Toast.makeText(
                    this@ConversationActivity,
                    R.string.message_send_failed,
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    private fun showMessageOptions(message: Message) {
        val options = mutableListOf("Copy text", "Delete message")

        MaterialAlertDialogBuilder(this)
            .setItems(options.toTypedArray()) { _, which ->
                when (which) {
                    0 -> copyMessageText(message)
                    1 -> confirmDeleteMessage(message)
                }
            }
            .show()
    }

    private fun copyMessageText(message: Message) {
        val clipboard = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("SMS", message.body)
        clipboard.setPrimaryClip(clip)
        Toast.makeText(this, R.string.copied_to_clipboard, Toast.LENGTH_SHORT).show()
    }

    private fun confirmDeleteMessage(message: Message) {
        MaterialAlertDialogBuilder(this)
            .setTitle("Delete message")
            .setMessage("Delete this message?")
            .setPositiveButton("Delete") { _, _ ->
                lifecycleScope.launch {
                    withContext(Dispatchers.IO) {
                        SmsHelper.deleteMessage(this@ConversationActivity, message.id)
                    }
                    loadMessages()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            android.R.id.home -> {
                finish()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}
