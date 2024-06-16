import requests
import json
import frappe



def send_message(campaign_name, mobile_no, template_params):
    url = frappe.db.get_single_value("Aisensy Settings").url
    api_key = frappe.db.get_single_value("Aisensy Settings").api_key
    user_name = frappe.db.get_single_value("Aisensy Settings").user_name

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
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response
