package com.kite.sms.adapter

import android.graphics.Typeface
import android.net.Uri
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.kite.sms.R
import com.kite.sms.model.Conversation

/**
 * RecyclerView adapter for the conversation list (inbox).
 */
class ConversationListAdapter(
    private val onConversationClick: (Conversation) -> Unit,
    private val onConversationLongClick: (Conversation) -> Boolean
) : ListAdapter<Conversation, ConversationListAdapter.ViewHolder>(ConversationDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_conversation, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val avatarImage: ImageView = itemView.findViewById(R.id.avatar_image)
        private val avatarText: TextView = itemView.findViewById(R.id.avatar_text)
        private val nameText: TextView = itemView.findViewById(R.id.text_name)
        private val snippetText: TextView = itemView.findViewById(R.id.text_snippet)
        private val timeText: TextView = itemView.findViewById(R.id.text_time)
        private val unreadBadge: View = itemView.findViewById(R.id.unread_badge)

        fun bind(conversation: Conversation) {
            nameText.text = conversation.displayName
            snippetText.text = conversation.snippet
            timeText.text = conversation.formattedTime

            // Set bold for unread conversations
            if (!conversation.isRead) {
                nameText.setTypeface(null, Typeface.BOLD)
                snippetText.setTypeface(null, Typeface.BOLD)
                timeText.setTypeface(null, Typeface.BOLD)
                unreadBadge.visibility = View.VISIBLE
            } else {
                nameText.setTypeface(null, Typeface.NORMAL)
                snippetText.setTypeface(null, Typeface.NORMAL)
                timeText.setTypeface(null, Typeface.NORMAL)
                unreadBadge.visibility = View.GONE
            }

            // Avatar
            if (conversation.photoUri != null) {
                avatarImage.setImageURI(Uri.parse(conversation.photoUri))
                avatarImage.visibility = View.VISIBLE
                avatarText.visibility = View.GONE
            } else {
                avatarImage.visibility = View.GONE
                avatarText.visibility = View.VISIBLE
                avatarText.text = conversation.initials
            }

            itemView.setOnClickListener { onConversationClick(conversation) }
            itemView.setOnLongClickListener { onConversationLongClick(conversation) }
        }
    }

    class ConversationDiffCallback : DiffUtil.ItemCallback<Conversation>() {
        override fun areItemsTheSame(oldItem: Conversation, newItem: Conversation): Boolean {
            return oldItem.threadId == newItem.threadId
        }

        override fun areContentsTheSame(oldItem: Conversation, newItem: Conversation): Boolean {
            return oldItem == newItem
        }
    }
}
