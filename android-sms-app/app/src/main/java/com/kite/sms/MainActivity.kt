package com.kite.sms

import android.app.role.RoleManager
import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SearchView
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.kite.sms.adapter.ConversationListAdapter
import com.kite.sms.model.Conversation
import com.kite.sms.util.NotificationHelper
import com.kite.sms.util.PermissionHelper
import com.kite.sms.util.SmsHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Main activity showing the list of SMS conversations (inbox).
 */
class MainActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var emptyView: TextView
    private lateinit var adapter: ConversationListAdapter
    private var allConversations = listOf<Conversation>()

    private val defaultSmsLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        // Refresh after returning from default SMS prompt
        loadConversations()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Create notification channel
        NotificationHelper.createNotificationChannel(this)

        setupToolbar()
        setupViews()
        setupAdapter()

        // Request permissions
        if (!PermissionHelper.hasSmsPermissions(this)) {
            PermissionHelper.requestAllPermissions(this)
        } else {
            loadConversations()
            promptDefaultSmsApp()
        }
    }

    override fun onResume() {
        super.onResume()
        if (PermissionHelper.hasSmsPermissions(this)) {
            loadConversations()
        }
    }

    private fun setupToolbar() {
        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        setSupportActionBar(toolbar)
        supportActionBar?.title = getString(R.string.app_name)
    }

    private fun setupViews() {
        recyclerView = findViewById(R.id.recycler_conversations)
        swipeRefresh = findViewById(R.id.swipe_refresh)
        emptyView = findViewById(R.id.text_empty)

        val fab = findViewById<FloatingActionButton>(R.id.fab_compose)
        fab.setOnClickListener {
            startActivity(Intent(this, ComposeActivity::class.java))
        }

        swipeRefresh.setOnRefreshListener {
            loadConversations()
        }
    }

    private fun setupAdapter() {
        adapter = ConversationListAdapter(
            onConversationClick = { conversation ->
                openConversation(conversation)
            },
            onConversationLongClick = { conversation ->
                showConversationOptions(conversation)
                true
            }
        )

        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter
    }

    private fun loadConversations() {
        lifecycleScope.launch {
            swipeRefresh.isRefreshing = true

            val conversations = withContext(Dispatchers.IO) {
                SmsHelper.getConversations(this@MainActivity)
            }

            allConversations = conversations
            adapter.submitList(conversations)

            swipeRefresh.isRefreshing = false
            emptyView.visibility = if (conversations.isEmpty()) View.VISIBLE else View.GONE
            recyclerView.visibility = if (conversations.isEmpty()) View.GONE else View.VISIBLE
        }
    }

    private fun openConversation(conversation: Conversation) {
        val intent = Intent(this, ConversationActivity::class.java).apply {
            putExtra(ConversationActivity.EXTRA_THREAD_ID, conversation.threadId)
            putExtra(ConversationActivity.EXTRA_ADDRESS, conversation.address)
            putExtra(ConversationActivity.EXTRA_DISPLAY_NAME, conversation.displayName)
        }
        startActivity(intent)
    }

    private fun showConversationOptions(conversation: Conversation) {
        MaterialAlertDialogBuilder(this)
            .setTitle(conversation.displayName)
            .setItems(arrayOf("Delete conversation")) { _, which ->
                when (which) {
                    0 -> confirmDeleteConversation(conversation)
                }
            }
            .show()
    }

    private fun confirmDeleteConversation(conversation: Conversation) {
        MaterialAlertDialogBuilder(this)
            .setTitle("Delete conversation")
            .setMessage("Delete all messages with ${conversation.displayName}?")
            .setPositiveButton("Delete") { _, _ ->
                lifecycleScope.launch {
                    withContext(Dispatchers.IO) {
                        SmsHelper.deleteThread(this@MainActivity, conversation.threadId)
                    }
                    loadConversations()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun promptDefaultSmsApp() {
        val roleManager = getSystemService(RoleManager::class.java)
        if (!roleManager.isRoleHeld(RoleManager.ROLE_SMS)) {
            val intent = roleManager.createRequestRoleIntent(RoleManager.ROLE_SMS)
            defaultSmsLauncher.launch(intent)
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)

        val searchItem = menu.findItem(R.id.action_search)
        val searchView = searchItem.actionView as SearchView
        searchView.queryHint = "Search messages..."

        searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                query?.let { filterConversations(it) }
                return true
            }

            override fun onQueryTextChange(newText: String?): Boolean {
                if (newText.isNullOrEmpty()) {
                    adapter.submitList(allConversations)
                } else {
                    filterConversations(newText)
                }
                return true
            }
        })

        searchItem.setOnActionExpandListener(object : MenuItem.OnActionExpandListener {
            override fun onMenuItemActionExpand(item: MenuItem): Boolean = true
            override fun onMenuItemActionCollapse(item: MenuItem): Boolean {
                adapter.submitList(allConversations)
                return true
            }
        })

        return true
    }

    private fun filterConversations(query: String) {
        val filtered = allConversations.filter { conversation ->
            conversation.displayName.contains(query, ignoreCase = true) ||
                conversation.snippet.contains(query, ignoreCase = true) ||
                conversation.address.contains(query, ignoreCase = true)
        }
        adapter.submitList(filtered)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            PermissionHelper.REQUEST_SMS_PERMISSIONS -> {
                if (PermissionHelper.allPermissionsGranted(grantResults)) {
                    loadConversations()
                    promptDefaultSmsApp()
                } else {
                    emptyView.text = getString(R.string.permission_required)
                    emptyView.visibility = View.VISIBLE
                }
            }
        }
    }
}
