# Copyright (c) 2024, Rahul and contributors
# For license information, please see license.txt

import json
import requests
import frappe
from frappe.model.document import Document
from frappe.core.doctype.server_script.server_script_utils import EVENT_MAP


class AisensyNotification(Document):
    def send_template_message(self, doc: Document):
        template_params = []
        mobile_no = frappe.db.get_value(self.reference_document_type, doc.name, self.field_name)
        for row in self.fields:
            field_value = frappe.db.get_value(self.reference_document_type, doc.name, row.field_name)
            template_params.append(field_value)
        send_message_api(self, mobile_no, template_params, doc.doctype, doc.name)


def send_message_api(self, mobile_no, template_params, doctype_name, record_name):
    url = frappe.db.get_single_value("Aisensy Settings", "url")
    api_key = frappe.db.get_single_value("Aisensy Settings", "api_key")
    user_name = frappe.db.get_single_value("Aisensy Settings", "user_name")
    host_url = frappe.db.get_single_value("Aisensy Settings", "host_url")
    default_image_url = frappe.db.get_single_value("Aisensy Settings", "default_image_url")
    file_url = attachment_url(self, doctype_name, record_name)

    payload = {
                "apiKey": api_key,
                "campaignName": self.campaign_name,
                "destination": mobile_no,
                "userName": user_name,
                "templateParams": template_params,
            }
    
    if self.send_attachment and file_url:
        file_url = host_url+file_url
        media_payload = {"media": {"url": file_url,
                       "filename": "demo-file"
                        }}
    else:
        media_payload = {"media": {"url": default_image_url,
                       "filename": "demo-file"
                        }}
    payload.update(media_payload)
    payload = json.dumps(payload)
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.request("POST", url, headers=headers, data=payload)

        frappe.get_doc({
            "doctype": "Aisensy Notification Log",
            "api_status": "Success",
            "response" : response,
            "source_doctype": doctype_name,
            "document_name": record_name,
            "api_response": response.text
        }).save(ignore_permissions=True)
    except Exception as e:
        frappe.msgprint(f"Failed to trigger Aisensy message",
            indicator="red",
            alert=True
        )
        frappe.get_doc({
            "doctype": "Aisensy Notification Log",
            "api_status": "Failed",
            "response" : response,
            "source_doctype": doctype_name,
            "document_name": record_name,
            "api_response": e
        }).insert()


def run_server_script_for_doc_event(doc, event):
    """Run on each event."""
    if event not in EVENT_MAP:
        return

    if frappe.flags.in_install:
        return

    if frappe.flags.in_migrate:
        return
    notification = get_notifications_map().get(doc.doctype, {})
    notification = notification.get(EVENT_MAP[event], None)
    if notification:
        for notification_name in notification:
            frappe.get_doc("Aisensy Notification",notification_name).send_template_message(doc)
            

def get_notifications_map():
    """Get mapping."""
    if frappe.flags.in_patch and not frappe.db.table_exists("Aisensy Notification"):
        return {}

    notification_map = {}
    enabled_aisensy_notifications = frappe.get_all(
        "Aisensy Notification",
        fields=("name", "reference_document_type", "doctype_event"),
        filters={"disabled": 0},
    )
    for notification in enabled_aisensy_notifications:
            notification_map.setdefault(
                notification.reference_document_type, {}
            ).setdefault(
                notification.doctype_event, []
            ).append(notification.name)
    return notification_map


def attachment_url(self, doctype_name, record_name):
    if not self.send_attachment:
        return
    file_url = frappe.db.get_value("File", {"attached_to_doctype": doctype_name, "attached_to_name": record_name}, "file_url")
    return file_url
