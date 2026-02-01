package com.kite.sms.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.kite.sms.R
import com.kite.sms.model.Message

/**
 * RecyclerView adapter for messages within a conversation.
 * Uses two view types for sent and received message bubbles.
 */
class MessageAdapter(
    private val onMessageLongClick: (Message) -> Boolean
) : ListAdapter<MessageAdapter.MessageItem, RecyclerView.ViewHolder>(MessageDiffCallback()) {

    companion object {
        private const val VIEW_TYPE_SENT = 0
        private const val VIEW_TYPE_RECEIVED = 1
        private const val VIEW_TYPE_DATE_HEADER = 2
    }

    /**
     * Wrapper to include date headers between message groups.
     */
    sealed class MessageItem {
        data class DateHeader(val date: String) : MessageItem()
        data class MessageEntry(val message: Message) : MessageItem()
    }

    /**
     * Convert a flat list of messages into a list with date headers.
     */
    fun submitMessages(messages: List<Message>) {
        val items = mutableListOf<MessageItem>()
        var lastDate = ""

        for (message in messages) {
            val date = message.formattedDate
            if (date != lastDate) {
                items.add(MessageItem.DateHeader(date))
                lastDate = date
            }
            items.add(MessageItem.MessageEntry(message))
        }

        submitList(items)
    }

    override fun getItemViewType(position: Int): Int {
        return when (val item = getItem(position)) {
            is MessageItem.DateHeader -> VIEW_TYPE_DATE_HEADER
            is MessageItem.MessageEntry -> {
                if (item.message.isSent) VIEW_TYPE_SENT else VIEW_TYPE_RECEIVED
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        return when (viewType) {
            VIEW_TYPE_SENT -> {
                val view = LayoutInflater.from(parent.context)
                    .inflate(R.layout.item_message_sent, parent, false)
                SentMessageViewHolder(view)
            }
            VIEW_TYPE_RECEIVED -> {
                val view = LayoutInflater.from(parent.context)
                    .inflate(R.layout.item_message_received, parent, false)
                ReceivedMessageViewHolder(view)
            }
            VIEW_TYPE_DATE_HEADER -> {
                val view = LayoutInflater.from(parent.context)
                    .inflate(R.layout.item_date_header, parent, false)
                DateHeaderViewHolder(view)
            }
            else -> throw IllegalArgumentException("Unknown view type: $viewType")
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        when (val item = getItem(position)) {
            is MessageItem.DateHeader -> (holder as DateHeaderViewHolder).bind(item.date)
            is MessageItem.MessageEntry -> {
                when (holder) {
                    is SentMessageViewHolder -> holder.bind(item.message)
                    is ReceivedMessageViewHolder -> holder.bind(item.message)
                }
            }
        }
    }

    inner class SentMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val bodyText: TextView = itemView.findViewById(R.id.text_message_body)
        private val timeText: TextView = itemView.findViewById(R.id.text_message_time)

        fun bind(message: Message) {
            bodyText.text = message.body
            timeText.text = message.formattedTime

            itemView.setOnLongClickListener { onMessageLongClick(message) }
        }
    }

    inner class ReceivedMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val bodyText: TextView = itemView.findViewById(R.id.text_message_body)
        private val timeText: TextView = itemView.findViewById(R.id.text_message_time)

        fun bind(message: Message) {
            bodyText.text = message.body
            timeText.text = message.formattedTime

            itemView.setOnLongClickListener { onMessageLongClick(message) }
        }
    }

    class DateHeaderViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val dateText: TextView = itemView.findViewById(R.id.text_date)

        fun bind(date: String) {
            dateText.text = date
        }
    }

    class MessageDiffCallback : DiffUtil.ItemCallback<MessageItem>() {
        override fun areItemsTheSame(oldItem: MessageItem, newItem: MessageItem): Boolean {
            return when {
                oldItem is MessageItem.DateHeader && newItem is MessageItem.DateHeader ->
                    oldItem.date == newItem.date
                oldItem is MessageItem.MessageEntry && newItem is MessageItem.MessageEntry ->
                    oldItem.message.id == newItem.message.id
                else -> false
            }
        }

        override fun areContentsTheSame(oldItem: MessageItem, newItem: MessageItem): Boolean {
            return oldItem == newItem
        }
    }
}
