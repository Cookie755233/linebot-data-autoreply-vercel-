import os
import re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, FlexSendMessage, LocationSendMessage
)
from msg.carousel import *
from utils.ls_search import search_applicants_by_parcel, search_info_by_applicant
from msg.read import read_messages
from msg.reply import reply_applicant_search_results
from msg.carousel import Carousel

import msg._error_messages as ERROR_MESSAGE


line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


app = Flask(__name__)

# domain root
@app.route("/")
def home():
    return "Hello Cookie!"


@app.route("/webhook", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.type != "text":
        return

    user_message = event.message.text
    status, return_value = read_messages(user_message)
    
    match status:
        #? found something, return flex message
        case 201: 
            flex_message = reply_applicant_search_results(return_value)
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="Search results", 
                                contents=flex_message))
            
        case 202: 
            return
        
        #@ make tutorial flex message on how to use the app when raised errors
        #? found nothing, return THINGS_NOT_FOUND_ERROR
        case 301:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(ERROR_MESSAGE.APPLICANT_NOT_FOUND_ERROR))
        case 302: 
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(ERROR_MESSAGE.PARCEL_NOT_FOUND_ERROR))
        #? user input incorrect, return USER_INPUT_ERROR
        case 400:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(ERROR_MESSAGE.USER_INPUT_ERROR))
        
        #? else, or bugs 
        case _:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage('haha in development'))
    
    # if re.match("查詢地號", user_message):
    #     if not len(user_message.split('\n')) == 4:
    #         reply_message = CONST.PARCEL_NOT_FOUND_ERROR
    #         line_bot_api.reply_message(
    #             event.reply_token, 
    #             TextSendMessage(reply_message))
    #         return
            
    #     carousel_container = {"type": "carousel", "contents": []}
    #     _, district, section, parcel = user_message.split("\n")
    #     result = list(search_applicants_by_parcel(district, section, parcel))

    #     if not result:
    #         reply_message = f"查無「{district}{section}{parcel}地號」資料!"
    #         line_bot_api.reply_message(
    #             event.reply_token, 
    #             TextSendMessage(reply_message))
    #         return
            
    #     insert_parcel_search_result(result, carousel_container)
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         FlexSendMessage(alt_text="Search results", 
    #                         contents=carousel_container))
        
    # if re.match("查詢申請人", user_message):
    #     if len(user_message.split('\n')) != 2: 
    #         reply_message = CONST.APPLICANT_NOT_FOUND_ERROR
    #         line_bot_api.reply_message(
    #             event.reply_token, 
    #             TextSendMessage(reply_message))
    #         return
        
    #     carousel_container = {"type": "carousel", "contents": []}
    #     _, name = user_message.split('\n')
        
    #     result = list(search_info_by_applicant(name))
    #     if not result:
    #             reply_message = f"查無「{name}」資料!"
    #             line_bot_api.reply_message(
    #                 event.reply_token, 
    #                 TextSendMessage(reply_message))
    #             return
        
    #     insert_applicant_search_result(result, carousel_container)
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         FlexSendMessage(alt_text="Search results", 
    #                         contents=carousel_container))

@line_handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data.startsWith('location'):
        longitude, latitude = re.findall(
            r'[0-9]*[.]?[0-9]+', event.postback.data)
        
        line_bot_api.reply_message(
            event.reply_token,
            LocationSendMessage(
                title = "TITLE",
                address = "ADDRESS",
                latitude = longitude,
                longitude = latitude
                )
            )   

if __name__ == "__main__":
    app.run(debug=True)
