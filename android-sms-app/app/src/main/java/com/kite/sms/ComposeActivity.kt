package com.kite.sms

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.MenuItem
import android.view.View
import android.widget.EditText
import android.widget.ImageButton
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.kite.sms.adapter.ContactSearchAdapter
import com.kite.sms.util.ContactHelper
import com.kite.sms.util.PermissionHelper
import com.kite.sms.util.SmsHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Activity for composing a new SMS message.
 * Includes contact search and autocomplete.
 */
class ComposeActivity : AppCompatActivity() {

    private lateinit var recipientInput: EditText
    private lateinit var messageInput: EditText
    private lateinit var sendButton: ImageButton
    private lateinit var contactList: RecyclerView
    private lateinit var contactAdapter: ContactSearchAdapter

    private var selectedAddress: String? = null
    private val searchHandler = Handler(Looper.getMainLooper())
    private var searchRunnable: Runnable? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_compose)

        setupToolbar()
        setupViews()
        handleIntent()
    }

    private fun setupToolbar() {
        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        setSupportActionBar(toolbar)
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            title = getString(R.string.new_message)
        }
    }

    private fun setupViews() {
        recipientInput = findViewById(R.id.edit_recipient)
        messageInput = findViewById(R.id.edit_message)
        sendButton = findViewById(R.id.button_send)
        contactList = findViewById(R.id.recycler_contacts)

        // Contact search adapter
        contactAdapter = ContactSearchAdapter { contact ->
            selectedAddress = contact.phoneNumber
            recipientInput.setText(contact.name)
            recipientInput.clearFocus()
            contactList.visibility = View.GONE
            messageInput.requestFocus()
        }

        contactList.layoutManager = LinearLayoutManager(this)
        contactList.adapter = contactAdapter

        // Recipient text watcher for contact search
        recipientInput.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: android.text.Editable?) {
                selectedAddress = null
                val query = s?.toString()?.trim() ?: ""
                debounceContactSearch(query)
            }
        })

        recipientInput.setOnFocusChangeListener { _, hasFocus ->
            if (!hasFocus) {
                contactList.visibility = View.GONE
            }
        }

        // Send button
        sendButton.setOnClickListener { sendMessage() }

        // Enable send button based on input
        val textWatcher = object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: android.text.Editable?) {
                updateSendButton()
            }
        }

        messageInput.addTextChangedListener(textWatcher)
        updateSendButton()
    }

    private fun handleIntent() {
        // Handle sms: and smsto: intents
        val uri = intent.data
        if (uri != null) {
            val address = uri.schemeSpecificPart
            if (!address.isNullOrEmpty()) {
                selectedAddress = address
                recipientInput.setText(address)

                // Try to resolve contact name
                lifecycleScope.launch {
                    val name = withContext(Dispatchers.IO) {
                        ContactHelper.getContactName(this@ComposeActivity, address)
                    }
                    if (name != null) {
                        recipientInput.setText(name)
                    }
                    messageInput.requestFocus()
                }
            }
        }

        // Handle EXTRA_TEXT for message body
        val extraText = intent.getStringExtra(android.content.Intent.EXTRA_TEXT)
        if (!extraText.isNullOrEmpty()) {
            messageInput.setText(extraText)
        }
    }

    private fun debounceContactSearch(query: String) {
        searchRunnable?.let { searchHandler.removeCallbacks(it) }

        if (query.length < 2) {
            contactList.visibility = View.GONE
            return
        }

        if (!PermissionHelper.hasContactsPermission(this)) {
            return
        }

        searchRunnable = Runnable {
            lifecycleScope.launch {
                val results = withContext(Dispatchers.IO) {
                    ContactHelper.searchContacts(this@ComposeActivity, query)
                }

                if (results.isNotEmpty() && recipientInput.hasFocus()) {
                    contactAdapter.submitList(results)
                    contactList.visibility = View.VISIBLE
                } else {
                    contactList.visibility = View.GONE
                }
            }
        }

        searchHandler.postDelayed(searchRunnable!!, 300)
    }

    private fun updateSendButton() {
        val hasRecipient = recipientInput.text.isNotBlank()
        val hasMessage = messageInput.text.isNotBlank()
        val enabled = hasRecipient && hasMessage
        sendButton.isEnabled = enabled
        sendButton.alpha = if (enabled) 1.0f else 0.5f
    }

    private fun sendMessage() {
        val address = selectedAddress ?: recipientInput.text.toString().trim()
        val body = messageInput.text.toString().trim()

        if (address.isEmpty() || body.isEmpty()) {
            Toast.makeText(this, R.string.fill_all_fields, Toast.LENGTH_SHORT).show()
            return
        }

        sendButton.isEnabled = false

        lifecycleScope.launch {
            val success = withContext(Dispatchers.IO) {
                SmsHelper.sendSms(this@ComposeActivity, address, body)
            }

            if (success) {
                Toast.makeText(this@ComposeActivity, R.string.message_sent, Toast.LENGTH_SHORT)
                    .show()
                finish()
            } else {
                Toast.makeText(
                    this@ComposeActivity,
                    R.string.message_send_failed,
                    Toast.LENGTH_SHORT
                ).show()
                updateSendButton()
            }
        }
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
