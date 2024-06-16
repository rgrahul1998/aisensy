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
        send_message_api(self.campaign_name, mobile_no, template_params)


def send_message_api(campaign_name, mobile_no, template_params):
    url = frappe.db.get_single_value("Aisensy Settings", "url")
    api_key = frappe.db.get_single_value("Aisensy Settings", "api_key")
    user_name = frappe.db.get_single_value("Aisensy Settings", "user_name")

    payload = json.dumps({
    "apiKey": api_key,
    "campaignName": campaign_name,
    "destination": mobile_no,
    "userName": user_name,
    "templateParams": template_params,
    "media": {
        "url": "https://aisensy-project-media-library-stg.s3.ap-south-1.amazonaws.com/IMAGE/5f450b00f71d36faa1d02bc4/9884334_graffiti%20dsdjpg",
        "filename": "demo-file"
    }
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)

    return response


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
    # frappe.cache().set_value("aisensy_notification_map", notification_map)

    return notification_map