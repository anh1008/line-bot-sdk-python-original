# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
from argparse import ArgumentParser

import asyncio
import aiohttp
from aiohttp import web

import logging

from aiohttp.web_runner import TCPSite

from linebot import (
    AsyncLineBotApi, WebhookParser
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, LocationSendMessage, TemplateSendMessage
)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)


class Handler:
    def __init__(self, line_bot_api, parser):
        self.line_bot_api = line_bot_api
        self.parser = parser

    async def echo(self, request):
        signature = request.headers['X-Line-Signature']
        body = await request.text()

        try:
            events = self.parser.parse(body, signature)
        except InvalidSignatureError:
            return web.Response(status=400, text='Invalid signature')

        for event in events:
            if not isinstance(event, MessageEvent):
                continue
            if not isinstance(event.message, TextMessage):
                continue

            if "秘密" in event.message.text:
                reply_text = "中國娃娃魚"
            elif "營業時間" in event.message.text:
                reply_text = "以下是營業資訊:\n開放時間:\n週二至週六\n10:00-12:00 / 13:00-17:00"
            # elif re.search(r'\b營業時間\b', event.message.text):
            elif "時間" in event.message.text:
                reply_text = "以下是營業資訊:\n開放時間:\n週二至週六\n10:00-12:00 / 13:00-17:00\n※如遇颱風等災害，依臺北市政府公布停班標準配合休館；其餘休館時間依公告為主。\n\n固定休館:\n週日、週一、國定假日\n※免費參觀，不需購票\n注意事項:\n-蟾蜍山大客廳全面禁菸。\n-寵物請勿落地，導盲犬不在此限。\n-聚落巷弄除一般參觀拍攝外，任何機關團體、公司行號拍攝影片或廣告，請向台北市電影委員會提出申請。"
            # elif re.search(r'\b蟾蜍山\b|\b蟾蜍山的位置\b|\b蟾蜍山在哪裡\b', event.message.text):
            elif "蟾蜍山" in event.message.text and "在哪裡" in event.message.text:
                # 回傳google地圖的連結做測試
                reply_text = "https://goo.gl/maps/cRfdA2Bequi2dXzb7"
            elif "蟾蜍山" in event.message.text and "位置" in event.message.text:
                # 測試位置有沒有反應
                reply_text = "已觸發位置條件"
                
                # if event.message.text == "蟾蜍山在哪裡":
                location_message = LocationSendMessage(
                    title='蟾蜍山', address='蟾蜍山', latitude=25.150481, longitude=121.778013)
                
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    location_message
                )
            elif "問題" in event.message.text and "選單" in event.message.text:
                buttons_template_message = TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://www.google.com/imgres?imgurl=http%3A%2F%2Fmeda.ntou.edu.tw%2Fmpedia%2Fthumb%2F1-0317-picture2_480.jpg&tbnid=Q8i9djioZtShwM&vet=12ahUKEwjIkMWC1J7-AhXBUt4KHc1BAR8QMygAegUIARDGAQ..i&imgrefurl=http%3A%2F%2Fmeda.ntou.edu.tw%2Fmpedia%2F%3Ft%3D1%26i%3D0317&docid=19oB1m2iB_i9VM&w=480&h=642&itg=1&q=%E4%B8%AD%E5%9C%8B%E5%A8%83%E5%A8%83%E9%AD%9A&ved=2ahUKEwjIkMWC1J7-AhXBUt4KHc1BAR8QMygAegUIARDGAQ',
                        title='中國娃娃魚',
                        text='Please select',
                        actions=[
                            PostbackAction(
                                label='postback',
                                display_text='postback text',
                                data='action=buy&itemid=1'
                            ),
                            MessageAction(
                                label='message',
                                text='測試'
                            ),
                            URIAction(
                                label='uri',
                                uri='https://zh.wikipedia.org/zh-tw/%E4%B8%AD%E5%9C%8B%E5%A4%A7%E9%AF%A2'
                            )
                        ]
                    )
                )
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    buttons_template_message
                )
            else:
                reply_text = "很抱歉我聽不懂你在說甚麼，請你換個方式再問一次"

            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        return web.Response(text="OK\n")
    
async def main(port=8000):
    session = aiohttp.ClientSession()
    async_http_client = AiohttpAsyncHttpClient(session)
    line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
    parser = WebhookParser(channel_secret)

    handler = Handler(line_bot_api, parser)

    app = web.Application()
    app.add_routes([web.post('/callback', handler.echo)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = TCPSite(runner=runner, port=port)
    await site.start()
    while True:
        await asyncio.sleep(3600)  # sleep forever


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    options = arg_parser.parse_args()

    asyncio.run(main(options.port))
