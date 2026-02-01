package com.kite.sms.adapter

import android.net.Uri
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.kite.sms.R
import com.kite.sms.util.ContactHelper

/**
 * RecyclerView adapter for contact search results in the compose screen.
 */
class ContactSearchAdapter(
    private val onContactClick: (ContactHelper.ContactResult) -> Unit
) : RecyclerView.Adapter<ContactSearchAdapter.ViewHolder>() {

    private var contacts = listOf<ContactHelper.ContactResult>()

    fun submitList(newContacts: List<ContactHelper.ContactResult>) {
        contacts = newContacts
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_contact, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(contacts[position])
    }

    override fun getItemCount(): Int = contacts.size

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val avatarImage: ImageView = itemView.findViewById(R.id.avatar_image)
        private val avatarText: TextView = itemView.findViewById(R.id.avatar_text)
        private val nameText: TextView = itemView.findViewById(R.id.text_name)
        private val numberText: TextView = itemView.findViewById(R.id.text_number)

        fun bind(contact: ContactHelper.ContactResult) {
            nameText.text = contact.name
            numberText.text = contact.phoneNumber

            if (contact.photoUri != null) {
                avatarImage.setImageURI(Uri.parse(contact.photoUri))
                avatarImage.visibility = View.VISIBLE
                avatarText.visibility = View.GONE
            } else {
                avatarImage.visibility = View.GONE
                avatarText.visibility = View.VISIBLE
                avatarText.text = contact.initials
            }

            itemView.setOnClickListener { onContactClick(contact) }
        }
    }
}
