import os
import unittest
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.keyboard_message import KeyboardMessage
from viberbot.api.messages.rich_media_message import RichMediaMessage
import requests
import logging
from flask import Flask, request, Response

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
import json



is_test = [False]

if(is_test[0]):
    AddressApiItilium = ""
    LoginItilium = ""
    PasswordItilium = ""
    auth_token_out = ""
else:
    AddressApiItilium = os.environ['AddressApiItilium']
    LoginItilium = os.environ['LoginItilium']
    PasswordItilium = os.environ["PasswordItilium"]
    auth_token_out = os.environ["AuthToken"]



#logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)
#handler = logging.StreamHandler()
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)
#logger.addHandler(handler)

# list_actions_senders = []

isDebug = [True]

class EmptyValue:
    empty = True

def print_debug(value):
    if isDebug[0] == True:
        print_value(value)


def GetTextCommand(message): #+
    text = ""
    if (isinstance(message, str)):
        text = message
    elif (isinstance(message, TextMessage)):
        text = message.text
    else:
        text = message.text
    return text

def print_value(object_to_print, value: str = "-----------------------------"):
    print(value + "{}".format(object_to_print))


class RatingIncidents:
    def __init__(self):
        self.need_rating: bool = False
        self.rating_exist: bool = True
        self.five_need_comment: bool = True
        self.four_need_comment: bool = True
        self.three_need_comment: bool = True
        self.two_need_comment: bool = False
        self.one_need_comment: bool = False


class StartedAction:
    def __init__(self, name: str, additional):
        self.name = name
        self.additional = additional

    def get_additional_for_JSON(self): #+
        print_debug(self.additional)
        if isinstance(self.additional, dict):
            temp_dict = {}
            for key in self.additional:
                if isinstance(self.additional[key], list):
                    temp = []
                    for item in self.additional[key]:
                        if isinstance(item, WrapperView) or isinstance(item, RatingIncidents):
                            temp.append(item.__dict__)
                        else:
                            temp.append(item)
                    temp_dict[key] = temp
                elif isinstance(self.additional[key], RatingIncidents):
                    temp_dict[key] = self.additional[key].__dict__
                else:
                    temp_dict[key] = self.additional[key]
            return temp_dict
        else:
            return self.additional

    def get_dict(self):#+
        return {"name": self.name, "additional": self.get_additional_for_JSON()}


class JobItilium:


    def get_state(self, environ, sender):
        print_debug("def get_state")
        quote = "\""
        data_to_send = """{
                                                           "data": {
                                                           "action": "get_state",
                                                           "type": """ + quote + environ + quote + """,
                                                           "sender": """ + quote + sender + quote + """,                                  
                                                           }
                                                        }"""

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            # print_value(description)

            # print_value(list)
            if (code == 200):
                answer.status = True
                if description == "":
                    answer.result = ""
                else:
                    answer.result = json.loads(description)
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def set_state(self, sender, environ,  state):
        print_debug("def get_state")
        quote = "\""
        data_to_send = json.dumps({ "data" : {
            "action" : "set_state",
            "sender" : sender,
            "type": environ,
            "state" : state
        }})

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            # print_value(description)

            # print_value(list)
            if (code == 200):
                answer.status = True
                answer.result = ""
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def not_exist(self, sender, Login = "", Password = "", Adress = "" ):
        print_debug("not_exist(self, sender, Login = "", Password = "", Adress = "" )")
        if(Login == ""):
            Login = LoginItilium
        if Password == "":
            Password = PasswordItilium
        if Adress == "":
            Adress = AddressApiItilium
        try:
            quote = "\""
            response = requests.post(Adress, data = """{
                                                                  "data": {
                                                                    "action": "non_exist",
                                                                    "sender": """ + quote + sender + quote+ """, 
                                                                  }
                                                                }""",
                                                        auth=(Login,Password))
            code = response.status_code
            description = response.text

            answer = Answer()
            answer.description = description

            if(code == 200):
                answer.status = True
                answer.result = description
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer


    def register(self, sender, message,  Login = "", Password = "", Adress = ""):
        print_debug("def register")
        if (Login == ""):
            Login = LoginItilium
        if Password == "":
            Password = PasswordItilium
        if Adress == "":
            Adress = AddressApiItilium
        text = GetTextCommand(message)

        try:
            quote = "\""
            response = requests.post(Adress, data=json.dumps({
                                                                "data": {
                                                                "action": "register",
                                                                "sender": sender,
                                                                "phone":  text
                                                                }
                                                            }).encode('utf-8'),
                                 auth=(Login, Password))
            code = response.status_code
            description = response.text
            answer = Answer()
            if (code == 200):
                answer.status = True
                answer.result = description
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer


    def get_last_conversations(self, sender):
        print_debug("def get_last_conversations")
        quote = "\""
        data_to_send = """{
                                                "data": {
                                                "action": "get_last_conversations",
                                                "sender": """ + quote + sender + quote + """,                                  
                                                }
                                             }"""

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            # print_value(description)

            # print_value(list)
            if (code == 200):
                answer.status = True
                list = json.loads(description)
                list_ret = []
                for incident in list:
                    list_ret.append(WrapperView(incident.get('view'), incident.get('detail_view'), incident.get('id')))
                answer.result = list_ret
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def confirm_incident(self, sender, reference_incident, rating, comment):
        print_debug("def confirm_incident")
        quote = "\""
        data_to_send = """{
                                          "data": {
                                          "action": "confirm_incident",
                                          "sender": """ + quote + sender + quote + """,
                                          "incident": """ + quote + reference_incident + quote + """,
                                          "rating": """ + quote + str(rating) + quote + """,
                                          "comment": """ + quote + comment + quote + """,                                  
                                          }
                                       }"""
        # print_value(data_to_send)

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            # response = requests.post(AddressApiItilium, data=data_to_send,
            #                          auth=(LoginItilium, PasswordItilium))
            code = response.status_code
            description = response.text
            answer = Answer()
            if (code == 200):
                answer.status = True
                answer.result = description
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def get_rating_for_incidents_confirmation(self, sender, incident_ref):
        print_debug("def get_rating_for_incidents_confirmation")
        quote = "\""
        data_to_send = """{
                                                  "data": {
                                                  "action": "get_rating_for_incidents_confirmation",
                                                  "incident": """ + quote + incident_ref + quote + """,
                                                  "sender": """ + quote + sender + quote + """,                                  
                                                  }
                                               }"""

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            if (code == 200):
                answer.status = True
                rating = RatingIncidents()
                dictionary = json.loads(description)
                rating.five_need_comment = dictionary.get('five_need_comment')
                rating.four_need_comment = dictionary.get('four_need_comment')
                rating.three_need_comment = dictionary.get('three_need_comment')
                rating.two_need_comment = dictionary.get('two_need_comment')
                rating.one_need_comment = dictionary.get('one_need_comment')
                rating.need_rating = dictionary.get('need_rating')
                rating.rating_exist = dictionary.get('rating_exist')
                answer.result = rating
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer


    def get_list_need_confirmed_incidents(self, sender):
        print_debug("def get_list_need_confirmed_incidents")
        quote = "\""
        data_to_send = """{
                                          "data": {
                                          "action": "list_need_confirmed_incidents",
                                          "sender": """ + quote + sender + quote + """,                                  
                                          }
                                       }"""

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            # print_value(description)

            # print_value(list)
            if (code == 200):
                answer.status = True
                list = json.loads(description)
                list_ret = []
                for incident in list:
                    list_ret.append(WrapperView(incident.get('view'), incident.get('detail_view'), incident.get('id')))
                answer.result = list_ret
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def decline_incident(self, sender, reference_incident, comment):
        print_debug("def decline_incident")
        quote = "\""
        data_to_send = """{
                                  "data": {
                                  "action": "decline_incident",
                                  "sender": """ + quote + sender + quote + """,
                                  "incident": """ + quote + reference_incident + quote + """,
                                  "comment": """ + quote + comment + quote + """,                                  
                                  }
                               }"""
        # print_value(data_to_send)

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            # response = requests.post(AddressApiItilium, data=data_to_send,
            #                          auth=(LoginItilium, PasswordItilium))
            code = response.status_code
            description = response.text
            answer = Answer()
            if (code == 200):
                answer.status = True
                answer.result = description
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def register_new_incident(self, message: str, sender: str):
        print_debug("def register_new_incident")
        quote = "\""
        message = message
        data_to_send = """{
                           "data": {
                           "action": "registration",
                           "sender": """ + quote + sender + quote + """,
                           "text":  """ + quote + message + quote + """,
                           }
                        }"""
        # print_value(data_to_send)

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'),auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            # response = requests.post(AddressApiItilium, data=data_to_send,
            #                          auth=(LoginItilium, PasswordItilium))
            code = response.status_code
            description = response.text
            answer = Answer()
            if (code == 200):
                answer.status = True
                answer.result = description
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def add_conversation(self, sender: str, reference_incident: str, text: str):
        print_debug("def add_conversation")
        quote = "\""
        data_to_send = """{
                                          "data": {
                                          "action": "add_converstaion",
                                          "sender": """ + quote + sender + quote + """,
                                          "text": """ + quote + text + quote + """,
                                          "incident": """ + quote + reference_incident + quote + """,                                  
                                          }
                                       }"""

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            # print_value(description)

            if (code == 200):
                answer.status = True
                answer.result = description
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer

    def get_list_open_incidents(self, sender):
        print_debug("def get_list_open_incidents")
        quote = "\""
        data_to_send = """{
                                  "data": {
                                  "action": "list_open_incidents",
                                  "sender": """ + quote + sender + quote + """,                                  
                                  }
                               }"""

        headers = {'Content-Type': 'text/xml; charset=utf-8', }
        try:
            req = requests.Request('POST', AddressApiItilium,
                                   headers=headers,
                                   data=data_to_send.encode('utf-8'), auth=(LoginItilium, PasswordItilium))
            prepped_requ = req.prepare()
            s = requests.Session()
            response = s.send(prepped_requ)

            code = response.status_code
            description = response.text
            answer = Answer()
            # print_value(description)

            # print_value(list)
            if (code == 200):
                answer.status = True
                list = json.loads(description)
                list_ret = []
                for incident in list:
                    list_ret.append(WrapperView(incident.get('view'), incident.get('detail_view'), incident.get('id')))
                answer.result = list_ret
            else:
                answer.status = False
                answer.description = description + " ERROR CODE:" + str(code)
            return answer
        except:
            answer = Answer()
            answer.description = "Ошибка соединения с Итилиум. Обратитесь к администратору."
            answer.status = False
            return answer


class WrapperView:
    def __init__(self, view: str, detail_view: str, id: str):
        self.view = view
        self.id = id

        self.detail_view = detail_view

class Answer:

    status: bool = True
    result = ""
    description: str = ""


class TemplatesKeyboards:

    @staticmethod
    def get_keyboard_cancel_confirm():
        return KeyboardMessage(keyboard=
        {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [{
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel",
                "Text": "Отменить подтверждение"
            }]
        }
        )

    @staticmethod
    def get_keyboard_cancel_decline():
        return KeyboardMessage(keyboard=
        {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [{
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel",
                "Text": "Отменить отклонение"
            }]
        }
        )

    @staticmethod
    def get_keyboard_rating_with_continue():

        buttons = []
        for i in '12345':
            value = 1
            if i == '5':
                value = 2
            buttons.append({
                "Columns": value,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_Confirm_rating_" + str(i),
                "Text": str(i)
            })
        buttons.append({
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "_Itilium_bot_Confirm_continue",
            "Text": "Продолжить без оценки"
        })
        buttons.append({
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "_Itilium_bot_Confirm_rating_cancel",
            "Text": "Отменить"
        })
        return KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons})

    @staticmethod
    def get_keyboard_rating():
        buttons = []
        for i in '12345':
            value = 1
            if i == '5':
                value = 2
            buttons.append({
                "Columns": value,
                "Rows":  1,
                "ActionBody": "_Itilium_bot_Confirm_rating_" + str(i),
                "Text": str(i)
            })
        buttons.append({
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "_Itilium_bot_Confirm_rating_cancel",
            "Text": "Отменить"
        })
        return KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons})

    @staticmethod
    def get_keyboard_on_show_conversation():
        return KeyboardMessage(min_api_version=4,
                               keyboard=
        {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [{
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_get_conversations_modify",
                "Text": "Ответить"
            }, {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_get_conversations_close",
                "Text": "Закрыть"
            }]
        }
        )

    @staticmethod
    def get_keyboard_confirm():
        return KeyboardMessage(min_api_version=4, keyboard=
        {
            "InputFieldState": "hidden",
            "Type": "keyboard",
            "Buttons": [{
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_Confirm",
                "Text": "Подтвердить"
            }, {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_Decline",
                "Text": "Отклонить"
            }, {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel_confirmation",
                "Text": "Отменить"
            }]
        }
        )

    @staticmethod
    def get_keyboard_cancel_modify():
        return KeyboardMessage(keyboard=
        {
            "Type": "keyboard",
            "Buttons": [{
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel_modify",
                "Text": "Отменить"
            }]
        }
        )

    @staticmethod
    def get_keyboard_cancel():
        return KeyboardMessage(keyboard=
        {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [{
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel",
                "Text": "Отменить регистрацию"
            }]
        }
        )

    @staticmethod
    def get_keyboard_cancel():
        return KeyboardMessage(keyboard=
        {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [{
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel",
                "Text": "Отменить регистрацию"
            }]
        }
        )

    @staticmethod
    def get_keyboard_start_message():
        return KeyboardMessage(min_api_version=4, keyboard=

        {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [{
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_new_incident",
                "Text": "Зарегистрировать"
            }, {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_get_last_conversations",
                "Text": "Последние сообщения",
            },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "_Itilium_bot_Modify",
                    "Text": "Внести уточнения"
                }, {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "_Itilium_bot_get_state",
                    "Text": "Получить статус обращений",
                }, {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "_Itilium_bot_get_need_confirmed",
                    "Text": "Обращения для подтверждения",
                }]
        }
        )

    @staticmethod
    def get_keyboard_select_incident_text(list, number_parts):#+
        max_buttons = 42
        if (len(list) > max_buttons ):
            count_in_part = max_buttons
            first_number = number_parts * count_in_part - count_in_part
            last_number = first_number + count_in_part - 1
            index = 0
            buttons = []
            isEnd = True
            for wrapper in list:
                if isinstance(wrapper, WrapperView):
                    id = wrapper.id
                    view = wrapper.view
                    detail_view = wrapper.detail_view
                else:
                    id = wrapper['id']
                    view = wrapper['view']
                    detail_view = wrapper['detail_view']

                if (index > last_number):
                    isEnd = False
                    break
                elif index >= first_number:
                    buttons.append({"TextVAlign": "top", "TextHAlign": "left", "ActionBody": id, "ActionType":"reply", "Text": view})
                index += 1
            buttons_keyboard = []
            if (isEnd == False):
                buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "_Itilium_bot_more_incidents", "Text":
                    "ЕЩЕ"})
            buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "_Itilium_bot_cancel_modify", "Text":
                "Отменить"})
            text_keyboard = {"Type": "keyboard","InputFieldState": "hidden", "Buttons": buttons_keyboard}
            return [RichMediaMessage(min_api_version=4, rich_media={"Type": "rich_media", "BgColor": "#FFFFFF",
                                                                   "Buttons":buttons}), KeyboardMessage(
                                                                            keyboard=text_keyboard, min_api_version=4)]
        else:
            text_keyboard = {"Type": "keyboard", "InputFieldState": "hidden"}
            buttons = []
            buttons_keyboard = []
            for wrapper in list:
                if isinstance(wrapper, WrapperView):
                    id = wrapper.id
                    view = wrapper.view
                    detail_view = wrapper.detail_view
                else:
                    id = wrapper['id']
                    view = wrapper['view']
                    detail_view = wrapper['detail_view']
                buttons.append({"TextVAlign": "top", "TextHAlign": "left", "ActionBody": id, "Text": view})
            buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "_Itilium_bot_cancel_modify", "Text": "Отменить"})
            text_keyboard.update({"Buttons": buttons_keyboard})
            return [RichMediaMessage(min_api_version=4, rich_media={"Type": "rich_media", "BgColor": "#FFFFFF",
                                                                   "Buttons":buttons}), KeyboardMessage(
                                                                            keyboard=text_keyboard, min_api_version=4)]

    @staticmethod
    def get_keyboard_cancel_or_continue_withont_comment():
        return KeyboardMessage(keyboard={
            "Type": "keyboard",
            "Buttons": [{
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_continue",
                "Text": "Продолжить без комментария"
            }, {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "_Itilium_bot_cancel",
                "Text": "Отменить"
            }]
        })


class JobMessage:

    def is_start_message(self, message: str):#+
        print_debug("is_start_message")
        if (message.startswith("_Itilium_bot_")):
            return False
        else:
            return True

    def get_start_message_answer(self):
        print_debug("get_start_message_answer")
        return [
            TextMessage(text="Добрый день! выберите интересующее вас действие."),
            TemplatesKeyboards.get_keyboard_start_message()
        ]

    def register_incident(self, job_itilium: JobItilium, message: str, sender: str):
        print_debug("register_incident")
        answer = job_itilium.register_new_incident(message, sender)
        if answer.status:
            return [TextMessage(text="Зарегистрировано обращение:" + answer.result),
                    TemplatesKeyboards.get_keyboard_start_message()]
        else:
            return [TextMessage(text="Не удалось зарегистировать обращение по причине:" + answer.description),
                    TemplatesKeyboards.get_keyboard_start_message()]

    def start_registration(self, sender: str):
        print_debug("start_registration")
        started_action = StartedAction("Registration", "")
        request_ok, description = SaveState(started_action,sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        print_debug("add started action")
        # print_debug("count:" + str(len(list_actions_senders)))
        return [TextMessage(text="Опишите вашу проблему."), TemplatesKeyboards.get_keyboard_cancel()]

    def start_itilium_modification(self, sender: str):
        print_debug("start_itilium_modification")
        job_itilium = JobItilium()
        answer = job_itilium.get_list_open_incidents(sender)
        if answer.status:
            list = answer.result
            if len(list) == 0:
                return [TextMessage(text="У вас нет зарегистрированных открытых обращений"),
                        TemplatesKeyboards.get_keyboard_start_message()]
            elif len(list) == 1:
                started_action = StartedAction("AddConversationsInputText", list[0].id)
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                    return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
                return [TextMessage(text="Введите уточнение:"), TextMessage(text=list[0].detail_view),
                        TemplatesKeyboards.get_keyboard_cancel_modify()]
            else:
                started_action = StartedAction("AddConversationsSelectIncident", {"number": 1, "list": list})
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                    return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

                list_answer = [TextMessage(text="Выберите обращение")]
                list_answer.extend(
                    TemplatesKeyboards.get_keyboard_select_incident_text(
                        list,started_action.additional.get("number")))

                print_debug(list_answer)
                return list_answer
        else:
            return [TextMessage(text="Ошибка." + answer.description),
                    TemplatesKeyboards.get_keyboard_start_message()]


    def start_get_state(self, sender: str):
        print_debug("start_get_state")
        job_itilium = JobItilium()
        answer = job_itilium.get_list_open_incidents(sender)
        if answer.status:
            list = answer.result
            if len(list) == 0:
                return [TextMessage(text="У вас нет зарегистрированных открытых обращений"),
                        TemplatesKeyboards.get_keyboard_start_message()]
            elif len(list) == 1:
                return [TextMessage(text="Детальная информация:"), TextMessage(text=list[0].detail_view),
                        TemplatesKeyboards.get_keyboard_start_message()]
            else:
                started_action = StartedAction("GetStateSelectIncident", {"number": 1, "list": list})
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                    return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

                list_answer = [TextMessage(text="Выберите обращение")]
                list_answer.extend(
                    TemplatesKeyboards.get_keyboard_select_incident_text(
                        list, started_action.additional.get("number")))
                return list_answer
        else:
            return [TextMessage(text="ошибка" + answer.description),
                    TemplatesKeyboards.get_keyboard_start_message()]

    def start_get_need_confirmed(self, sender: str):
        print_debug("start_get_need_confirmed")
        job_itilium = JobItilium()
        answer = job_itilium.get_list_need_confirmed_incidents(sender)
        if answer.status:
            list = answer.result
            if len(list) == 0:
                return [TextMessage(text="Нет обращений, требующих подтверждения"),
                        TemplatesKeyboards.get_keyboard_start_message()]
            elif len(list) == 1:
                started_action = StartedAction("GetConfirmed_SelectButtonsConfirmDecline", list[0].id)
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                     return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
                return [TextMessage(text="Подтвердите или отклоните выполнение обращения:"),
                        TextMessage(text=list[0].detail_view),
                        TemplatesKeyboards.get_keyboard_confirm()]
            else:
                started_action = StartedAction( "GetConfirmedSelectIncident", {"number": 1, "list": list})
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                    return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]


                list_answer = [TextMessage(text="Выберите обращение")]
                list_answer.extend(
                    TemplatesKeyboards.get_keyboard_select_incident_text(
                        list, started_action.additional.get("number")))

                return list_answer
        else:
            return [TextMessage(text="Ошибка" + answer.description),
                    TemplatesKeyboards.get_keyboard_start_message()]

    def start_get_last_conversations(self, sender):
        print_debug("start_get_last_conversations")
        job_itilium = JobItilium()
        answer = job_itilium.get_last_conversations(sender)
        if answer.status:
            list = answer.result

            if len(list) == 0:
                return [TextMessage(text="Нет сообщений за последние 5 дней"), TemplatesKeyboards.get_keyboard_start_message()]
            else:
                started_action = StartedAction("GetLastConversations", {"number": 1, "list": list})
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                    return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

                list_answer = [TextMessage(text="Выберите сообщение для уточнения или просмотра")]
                list_answer.extend(
                    TemplatesKeyboards.get_keyboard_select_incident_text(
                        list, started_action.additional.get("number")))
                return list_answer
        else:
            return [TextMessage(text="ошибка" + answer.description), TemplatesKeyboards.get_keyboard_start_message()]



    def on_command_select(self, message: str, sender: str):
        print_debug("on_command_select")
        if (message == "_Itilium_bot_new_incident"):
            return self.start_registration(sender)
        elif (message == "_Itilium_bot_Modify"):
            return self.start_itilium_modification(sender)
        elif (message == "_Itilium_bot_get_state"):
            return self.start_get_state(sender)
        elif (message == "_Itilium_bot_get_need_confirmed"):
            return self.start_get_need_confirmed(sender)
        elif (message == "_Itilium_bot_get_last_conversations"):
            return self.start_get_last_conversations(sender)
        else:
            return TextMessage(text="Не реализовано, обратитесь к разработчику")

    def get_started_action(self, sender: str):
        request_ok, value = GetState(sender)
        if request_ok:
            if isinstance(value, EmptyValue):
                return True, None
            elif value.get("value") == "" :
                return True, None
            else:
                return True, StartedAction(value["name"], value["additional"])
        else:
            return False, value

    def sender_has_started_actions(self, sender: str):
        request_ok, value = self.get_started_action(sender)
        if request_ok:
            return True, value != None
        else:
            return False, value


    def remove_started_action(self, sender: str):
        print_debug("remove_started_action")
        request_ok, description = SaveState("", sender)
        if request_ok == False:
            return False, [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        else:
            return True, EmptyValue()

    def continue_registration(self, message, sender: str):
        print_debug("continue_registration")
        job_itilium = JobItilium()
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        command = self.get_text_comand(message)
        if (command == "_Itilium_bot_cancel"):
            return [TextMessage(text="Регистрация отменена"), TemplatesKeyboards.get_keyboard_start_message()]
        else:
            return self.register_incident(job_itilium, command, sender)

    def continue_confirmed_input_comment(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_confirmed_input_comment")
        command = self.get_text_comand(message)
        reference_incident = started_action.additional.get("ref")
        rating = started_action.additional.get("rating")
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        if (command == "_Itilium_bot_cancel"):
            return [TextMessage(text="Подтверждение не выполнено."), TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_continue":  # Пользователю эта кнопка недоступна может быть, но он может ввести эту команду. На самом деле, если пользователь не хочет комментировать, то и не надо его заставлять
            job_itilium = JobItilium()
            answer = job_itilium.confirm_incident(sender, reference_incident, rating, "")
            if (answer == False):
                return [TextMessage(text="Не удалось подтвердить обращение по причине:" + answer.description)]
            else:
                return [TextMessage(text=answer.result), TemplatesKeyboards.get_keyboard_start_message()]
        else:  # Комментарий введен
            job_itilium = JobItilium()
            answer = job_itilium.confirm_incident(sender, reference_incident, rating, command)
            if (answer == False):
                return [TextMessage(text="Не удалось подтвердить обращение по причине:" + answer.description)]
            else:
                return [TextMessage(text=answer.result),TemplatesKeyboards.get_keyboard_start_message()]

    def continue_confirmed_select_rating(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_confirmed_select_rating")
        command = self.get_text_comand(message)
        reference_incident = started_action.additional.get("ref")
        rating_state: RatingIncidents = started_action.additional.get("rating_state")
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        if (command == "_Itilium_bot_Confirm_rating_cancel"):
            return [TextMessage(text="Подтверждение не выполнено."), TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_Confirm_continue":

            job_itilium = JobItilium()
            answer = job_itilium.confirm_incident(sender, reference_incident, -1,"")
            if (answer == False):
                return [TextMessage(text="Не удалось подтвердить обращение по причине:" + answer.description)]
            else:
                return [TextMessage(text=answer.result), TemplatesKeyboards.get_keyboard_start_message()]
        else:
            need_comment = False
            rating = -1
            if command == "_Itilium_bot_Confirm_rating_1":
                rating = 1
                if rating_state['one_need_comment'] == True:
                    need_comment = True
            elif command == "_Itilium_bot_Confirm_rating_2":
                rating = 2
                if rating_state['two_need_comment'] == True:
                    need_comment = True
            elif command == "_Itilium_bot_Confirm_rating_3":
                rating = 3
                if rating_state['three_need_comment'] == True:
                    need_comment = True
            elif command == "_Itilium_bot_Confirm_rating_4":
                rating = 4
                if rating_state['four_need_comment'] == True:
                    need_comment = True
            elif command == "_Itilium_bot_Confirm_rating_5":
                rating = 5
                if rating_state['five_need_comment'] == True:
                    need_comment = True

            started_action = StartedAction( "Get_Comfirmed_input_comment",
                                           {"ref": reference_incident, "rating": rating})
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            if need_comment:
                return [TextMessage(text="Данная оценка требует комментарий:"),
                        TemplatesKeyboards.get_keyboard_cancel_confirm()]
            else:
                return [TextMessage(text="Укажите комментарий к оценке"),
                        TemplatesKeyboards.get_keyboard_cancel_or_continue_withont_comment()]

    def continue_confirmed_select_buttons(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_confirmed_select_buttons")
        command = self.get_text_comand(message)
        reference_incident = started_action.additional
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        if (command == "_Itilium_bot_Confirm"):
            job_itilium = JobItilium()
            answer = job_itilium.get_rating_for_incidents_confirmation(sender, reference_incident)
            if answer.status:
                rating_state = answer.result
                # print_value(rating_state.need_rating)
                if rating_state.need_rating:
                    started_action = StartedAction( "Get_Comfirmed_select_rating",
                                                   {"ref": reference_incident, "rating_state": rating_state})
                    request_ok, description = SaveState(started_action, sender)
                    if request_ok == False:
                        return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
                    return [ TextMessage(text="Оцените выполнение обращения"), TemplatesKeyboards.get_keyboard_rating()]
                elif rating_state.rating_exist:
                    started_action = StartedAction( "Get_Comfirmed_select_rating",
                                                   {"ref": reference_incident, "rating_state": rating_state})
                    request_ok, description = SaveState(started_action, sender)
                    if request_ok == False:
                        return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
                    return [TextMessage(text="Оцените выполнение обращения"), TemplatesKeyboards.get_keyboard_rating_with_continue()]
                else:
                    job_itilium = JobItilium()
                    answer = job_itilium.confirm_incident(sender, reference_incident, -1, "")
                    if (answer == False):
                        return [TextMessage(text="Не удалось подтвердить обращение по причине:" + answer.description)]
                    else:
                        return [TextMessage(text=answer.result), TemplatesKeyboards.get_keyboard_start_message()]
            else:
                return [TextMessage(text=answer.description), TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_Decline":

            started_action = StartedAction( "Get_decline_input_comment",
                                           {"ref": reference_incident})
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            return [TextMessage(text="Укажите причину отклонения"),
                    TemplatesKeyboards.get_keyboard_cancel_decline()]


        else:  # cancel
            return [TextMessage(text="Подтверждение не выполнено."), TemplatesKeyboards.get_keyboard_start_message()]

    def continue_get_last_conversations_select_actions(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_get_last_conversations_select_actions")
        reference = started_action.additional
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        command = self.get_text_comand(message)
        if command == "_Itilium_bot_get_conversations_modify":
            started_action = StartedAction( "AddConversationsInputText", reference)
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            return [TextMessage(text="Введите уточнение"),
                    TemplatesKeyboards.get_keyboard_cancel_modify()]

        elif command == "_Itilium_bot_get_conversations_close":
            return [TemplatesKeyboards.get_keyboard_start_message()]



    def continue_get_last_conversations(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_get_last_conversations")
        list = started_action.additional.get("list")
        number_page = started_action.additional.get("number")
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

        command = self.get_text_comand(message)

        if (command == "_Itilium_bot_cancel_modify"):
            return [TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_more_incidents":
            started_action = StartedAction( "GetLastConversations",
                                           {"number": number_page + 1, "list": list})
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

            list_answer = TemplatesKeyboards.get_keyboard_select_incident_text(
                    list, number_page + 1)


            return list_answer
        else:
            started_action = StartedAction("GetLastConversation_select_action", command)
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            detail_view = ""
            for wrapper in list:
                if (wrapper['id'] == command):
                    detail_view = wrapper['detail_view']
                    break
            return [TextMessage(text="Детальная информация:"), TextMessage(text=detail_view),
                    TemplatesKeyboards.get_keyboard_on_show_conversation()]



    def continue_get_confirmed_select_incident(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_get_confirmed_select_incident")
        list = started_action.additional.get("list")
        number_page = started_action.additional.get("number")
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

        command = self.get_text_comand(message)
        if (command == "_Itilium_bot_cancel_modify"):
            return [TextMessage(text="Подтверждение не выполнено."),TemplatesKeyboards.get_keyboard_start_message()]
        if (command == "_Itilium_bot_cancel_confirmation"):
            return [TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_more_incidents":
            started_action = StartedAction( "GetConfirmedSelectIncident",
                                           {"number": number_page + 1, "list": list})
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

            list_answer = TemplatesKeyboards.get_keyboard_select_incident_text(
                list, number_page + 1)

            return list_answer
        else:
            started_action = StartedAction( "GetConfirmed_SelectButtonsConfirmDecline", command)
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            detail_view = ""
            for wrapper in list:
                if (wrapper['id'] == command):
                    detail_view = wrapper['detail_view']
                    break
            return [TextMessage(text="Подтвердите или отклоните выполнение обращения:"), TextMessage(text=detail_view),
                    TemplatesKeyboards.get_keyboard_confirm()]

    def continue_get_state_select_incident(self, message, sender, started_action: StartedAction):
        print_debug("continue_get_state_select_incident")
        list = started_action.additional.get("list")
        number_page = started_action.additional.get("number")
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

        command = self.get_text_comand(message)
        if (command == "_Itilium_bot_cancel_modify"):
            return [TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_more_incidents":
            started_action = StartedAction( "GetStateSelectIncident",
                                           {"number": number_page + 1, "list": list})
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]


            list_answer = TemplatesKeyboards.get_keyboard_select_incident_text(
                list, number_page + 1)

            return list_answer
        else:
            for wrapper in list:
                if (wrapper['id'] == command):
                    detail_view = wrapper['detail_view']
                    break
            return [TextMessage(text=detail_view), TemplatesKeyboards.get_keyboard_start_message()]

    def continue_add_conversations_select_incident(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_add_conversations_select_incident")
        list = started_action.additional.get("list")
        number_page = started_action.additional.get("number")
        command = self.get_text_comand(message)

        if (command == "_Itilium_bot_cancel_modify"):
            request_ok, description = self.remove_started_action(sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            return [TextMessage(text="Уточнения не внесены"), TemplatesKeyboards.get_keyboard_start_message()]
        elif command == "_Itilium_bot_more_incidents":
            request_ok, description = self.remove_started_action(sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            started_action = StartedAction("AddConversationsSelectIncident",
                                           {"number": number_page + 1, "list": list})
            request_ok, description = SaveState(started_action, sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]

            list_answer = TemplatesKeyboards.get_keyboard_select_incident_text(
                list, number_page + 1)
            return list_answer
        else:
            request_ok, description = self.remove_started_action(sender)
            if request_ok == False:
                return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
            started_action = StartedAction("AddConversationsInputText", command)

            detail_view = ""
            found = 0
            for wrapper in list:
                if (wrapper['id'] == command):
                    detail_view = wrapper['detail_view']
                    found = 1
                    break
            if (found == 1):
                request_ok, description = SaveState(started_action, sender)
                if request_ok == False:
                    return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
                return [TextMessage(text="Введите уточнение:"), TextMessage(text=detail_view),
                        TemplatesKeyboards.get_keyboard_cancel_modify()]
            return self.get_start_message_answer()  # Не то ввел пользователь. Сначала

    def continue_add_conversations_input_text(self, message, sender: str, started_action: StartedAction):
        print_debug("continue_add_conversations_input_text")
        command = self.get_text_comand(message)
        reference = started_action.additional
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        if (command == "_Itilium_bot_cancel_modify"):
            return [TextMessage(text="Уточнения не внесены"), TemplatesKeyboards.get_keyboard_start_message()]
        job_itilium = JobItilium()
        answer = job_itilium.add_conversation(sender, reference, command)
        print_debug("yttttttttttttttttttttttt:" + answer.description)
        if (answer.status == False):
            return [TextMessage(text="Не удалось внести уточнения по причине:{}".format(answer.description)),
                    TemplatesKeyboards.get_keyboard_start_message()]
        else:
            return [TextMessage(text=answer.result), TemplatesKeyboards.get_keyboard_start_message()]

    def continue_decline_incident_input_text(self, message, sender, started_action):
        print_debug("continue_decline_incident_input_text")
        command = self.get_text_comand(message)
        reference = started_action.additional.get("ref")
        request_ok, description = self.remove_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=description), TemplatesKeyboards.get_keyboard_start_message()]
        if (command == "_Itilium_bot_cancel"):
            return [TextMessage(text="Обращение не отклонено."), TemplatesKeyboards.get_keyboard_start_message()]
        else:
            job_itilium = JobItilium()
            answer = job_itilium.decline_incident(sender, reference, command)
            if (answer == False):
                return [TextMessage(text="Не удалось отклонить обращение по причине:" + answer.description),
                        TemplatesKeyboards.get_keyboard_start_message()]
            else:
                return [TextMessage(text=answer.result), TemplatesKeyboards.get_keyboard_start_message()]

    def continue_started_process(self, message, sender: str):
        print_debug("continue started process")
        request_ok, started_action = self.get_started_action(sender)
        if request_ok == False:
            return [TextMessage(text=started_action), TemplatesKeyboards.get_keyboard_start_message()]

        if (started_action.name == "Registration"):
            return self.continue_registration(message, sender)
        elif started_action.name == "GetConfirmed_SelectButtonsConfirmDecline":
            return self.continue_confirmed_select_buttons(message, sender, started_action)
        elif started_action.name == "Get_Comfirmed_input_comment":
            return self.continue_confirmed_input_comment(message, sender, started_action)
        elif started_action.name == "Get_Comfirmed_select_rating":
            return self.continue_confirmed_select_rating(message, sender, started_action)
        elif started_action.name == "GetConfirmedSelectIncident":
            return self.continue_get_confirmed_select_incident(message, sender, started_action)
        elif started_action.name == "GetLastConversations":
            return self.continue_get_last_conversations(message, sender, started_action)
        elif started_action.name == "GetLastConversation_select_action":
            return self.continue_get_last_conversations_select_actions(message, sender, started_action)
        elif started_action.name == "GetStateSelectIncident":
            return self.continue_get_state_select_incident(message, sender, started_action)
        elif started_action.name == "AddConversationsSelectIncident":
            return self.continue_add_conversations_select_incident(message, sender, started_action)
        elif started_action.name == "AddConversationsInputText":
            return self.continue_add_conversations_input_text(message, sender, started_action)
        elif started_action.name == "Get_decline_input_comment":
            return self.continue_decline_incident_input_text(message, sender, started_action)

        else:
            return [TextMessage(text="Не реализовано "), TemplatesKeyboards.get_keyboard_start_message()]

    def get_text_comand(self, message):
        print_debug("get_text_comand")
        return GetTextCommand(message)

    def first_level_comand(self, message, sender: str):
        print_debug("first level comand")
        text = self.get_text_comand(message)
        if (self.is_start_message(text)):
            return self.get_start_message_answer()
        else:
            return self.on_command_select(text, sender)

    def process(self, message, sender: str):
        print_debug("process")
        request_ok, has = self.sender_has_started_actions(sender)
        if request_ok == False:
            return [TextMessage(text=has), TemplatesKeyboards.get_keyboard_start_message()]
        if (has == False):
            print_debug("NO started action")
            return self.first_level_comand(message, sender)
        else:
            print_debug("has started action")
            return self.continue_started_process(message, sender)



class Integration:
    def on_new_message(self, message, sender: str):
        print_debug("on_new_message")
        job = JobMessage()
        retMessage = job.process(message, sender)
        return retMessage

    def on_subscribe(self, sender: str):
        return TextMessage(text="Спасибо, что подписались!")

    def on_failed_message(self, message: str, sender: str):
       # logger.warning("client failed receiving message. failure: {0}".format(message))
        pass



app = Flask(__name__)

viber = Api(BotConfiguration(
    name='Itilium-bot',
    avatar='http://site.com/avatar.jpg',
    auth_token=auth_token_out
))



def SaveValueToEnviron(value, NameEnviron, sender):
    job = JobItilium()
    answer = job.set_state(sender, NameEnviron, value)
    if answer.status:
        return True, ""
    else:
        return False, answer.description



def LoadValueFromEnviron(NameEnviron, sender):
    job = JobItilium()
    answer = job.get_state(NameEnviron, sender)
    if answer.status:
        data = answer.result
        if data == "":
            return True, EmptyValue()
        else:
            return True, data
    else:
        return False, answer.description

def SaveState(started_action, sender):
    if isinstance(started_action,StartedAction):
        return SaveValueToEnviron(started_action.get_dict(), "temp_data_fields", sender)
    else:
        return SaveValueToEnviron({"value":started_action}, "temp_data_fields", sender)

def GetState(sender):
    return LoadValueFromEnviron("temp_data_fields", sender)


def GetIsRegistration(sender):
    loadet, value = LoadValueFromEnviron("registration_fields", sender)
    if loadet:
        if isinstance(value, EmptyValue):
            return True, False
        else:
            if value.get("value"):
                return True, True
            else:
                return True, False
    else:
        return False, value


def SetIsRegistration(sender, state:bool ):
    return SaveValueToEnviron({"value":state}, "registration_fields", sender)

def VerifyRegistration(senderid, message ):

    print_debug("Verify registration")
    job_itilium = JobItilium()
    request_ok, state = GetIsRegistration(senderid)
    if request_ok:
        if state == False:
            print_debug("-Verify registration false")
            answer = job_itilium.not_exist(senderid)
            if answer.status:
                if (answer.result == str(1)):
                    print_debug("-Verify registration non exist")
                    ret = TextMessage(text="Укажите идентификатор подписчика")
                    request_ok, description = SetIsRegistration( senderid, True)
                    if request_ok == False:
                        return True, TextMessage(text=description)
                    # print_value("is registrations {}".format(GetIsRegistration(senderid)))
                    return  True, ret
                else:
                    print_debug("-Verify registration exist")
                    return False, EmptyValue()
            else:
                ret = TextMessage(text=answer.description)
                return True, ret
        elif state == True:
            print_debug("-Verify registration true")
            answer = job_itilium.register(senderid, message)
            if answer.status == True:
                if (answer.result == str(1)):
                    print_debug("-Verify registration register")
                    request_ok, description = SetIsRegistration(senderid, False)
                    if request_ok == False:
                        return True, TextMessage(text=description)
                    return False, EmptyValue()
                else:
                    ret = [TextMessage(text=answer.result),
                           TextMessage(text="Укажите идентификатор подписчика")]
                    return True, ret

            else:
                ret = TextMessage(text=answer.description)
                return True, ret
        else:
            return False, EmptyValue()
    else:
        ret = TextMessage(text=state)
        return True, ret


@app.route('/',  methods=['POST'])
def incoming():
    print_debug("incoming message")

    # print_debug("count started actions:" + str(len(list_actions_senders)))
    # logger.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method

    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    integration = Integration()

    if isinstance(viber_request, ViberMessageRequest):

        # print_debug("before test variable{}".format(w[0]))

        # viber.send_messages(viber_request.sender.id, TextMessage(text="..."))

        print_debug("incoming message:" + viber_request.message.text)
        # print_debug("before test variable{}".format(os.environ["test"]))
        # os.environ["test"] = os.environ["test"] + '1'
        # job = JobMessage()
        # print_debug("before sender_has_started_actions(sender) {}".format(job.sender_has_started_actions(viber_request.sender.id)))
        # print_debug("before sender_has_started_actions(sender) {}".format(os.environ["temp_data_fields"]))
        isReg, mess = VerifyRegistration(viber_request.sender.id, viber_request.message)

        if isReg:
            viber.send_messages(viber_request.sender.id, mess)

        else:
            viber.send_messages(viber_request.sender.id, integration.on_new_message(viber_request.message,
                                                                                    viber_request.sender.id))

        # print_debug("after sender_has_started_actions(sender) {}".format(job.sender_has_started_actions(viber_request.sender.id)))
        # print_debug("after sender_has_started_actions(sender) {}".format(os.environ["temp_data_fields"]))

    elif isinstance(viber_request, ViberSubscribedRequest):
        print_debug("subscribe message")
        viber.send_messages(viber_request.sender.id, integration.on_subscribe(viber_request.sender.id))
    elif isinstance(viber_request, ViberFailedRequest):
        print_debug("failed request")
        integration.on_failed_message(viber_request.message, viber_request.sender.id)
    else:
        print_debug("others")

    return Response(status=200)

# integration = Integration()
# senderid = "RH2xtdiCKsztWpOkGlMxZQ=="
########################################################################################################################
##          TESTS                                                            ###########################################
########################################################################################################################

class TestsStartedAction(unittest.TestCase):
    def test_StartedAction_getAdditional(self):
        started_actions = StartedAction("test", 1)
        left = started_actions.get_dict()

        self.assertEqual(left, {"name": "test", "additional": 1})
        self.assertNotEqual(left,{"name": "test", "additional": 2})
        self.assertNotEqual(left,{"name": "test2", "additional": 2})
        self.assertNotEqual(left,{"1name": "test", "additional": 2})
        self.assertNotEqual(left,{"name": "test", "1additional": 1})
        self.assertNotEqual(left,{"name": "test", "1additional": "1"})

        started_actions = StartedAction("test", "str")
        left = started_actions.get_dict()
        self.assertEqual(left, {"name": "test", "additional": "str"})
        self.assertNotEqual(left, {"name": "test", "additional": "str1"})
        self.assertNotEqual(left, {"name": "test2", "additional": "str"})
        self.assertNotEqual(left, {"1name": "test", "additional": "str"})
        self.assertNotEqual(left, {"name": "test", "1additional": "str"})
        self.assertNotEqual(left, {"name": "test", "additional": 1})

        started_actions = StartedAction("test", {"data":[WrapperView("1","2","3")]})
        left = started_actions.get_dict()
        self.assertEqual(left, {"name": "test", "additional": {"data":[{"view":"1","id":"3", "detail_view": "2"}]}})
        self.assertNotEqual(left, {"name": "test", "additional": "str"})

        started_actions = StartedAction("test", {"data": [RatingIncidents()]})
        left = started_actions.get_dict()
        self.assertEqual(left, {"name": "test", "additional": {"data": [{"need_rating": False, "rating_exist": True, "five_need_comment":
            True, "four_need_comment": True, "three_need_comment": True, "two_need_comment": False,
                                                                         "one_need_comment": False}]}})
        self.assertNotEqual(left, {"name": "test", "additional": "str"})

        started = StartedAction("Get_Comfirmed_select_rating",
                      {"ref": "reference", "rating_state": RatingIncidents()})
        dict = started.get_dict()
        right = {'name': 'Get_Comfirmed_select_rating', 'additional': {'ref': 'reference',
                                                               'rating_state': {'need_rating': False,
                                                                                'rating_exist': True,
                                                                                'five_need_comment': True,
                                                                                'four_need_comment': True,
                                                                                'three_need_comment': True,
                                                                                'two_need_comment': False,
                                                                                'one_need_comment': False}}}
        self.assertEqual( dict, right)


        started_actions = StartedAction("test", {"data": "123"})
        left = started_actions.get_dict()
        self.assertEqual(left, {"name": "test", "additional": {"data": "123"}})
        self.assertNotEqual(left, {"name": "test", "additional": {"data":[{"view":"1","id":"3", "detail_view": "2"}]}})


        started_actions = StartedAction("test", {"data": ["1",2, True]})
        left = started_actions.get_dict()
        self.assertEqual(left, {"name": "test", "additional": {"data": ["1", 2, True]}})
        self.assertNotEqual(left,
                            {"name": "test", "additional": {"data": [{"view": "1", "id": "3", "detail_view": "2"}]}})


class TestsOthers(unittest.TestCase):

    def test_GetTextCommand(self):
        self.assertEqual(GetTextCommand("привет"), "привет")
        self.assertNotEqual(GetTextCommand("привет"), "привет1")
        self.assertEqual(GetTextCommand(TextMessage(text="привет")), "привет")
        self.assertNotEqual(GetTextCommand(TextMessage(text="привет")), "привет1")

class TestJobMessage(unittest.TestCase):

    def test_is_start_message(self):
        job = JobMessage()
        self.assertFalse(job.is_start_message("_Itilium_bot_"))
        self.assertTrue(job.is_start_message("ttt"))

class TestJobItilium(unittest.TestCase):
    def test_not_exist(self):
        job = JobItilium()
        self.assertEqual(job.not_exist("123","kdkdkdkdkdkdk").status, False)

    # def test_get_set_state(self):
    #     job = JobItilium()
    #     left = job.set_state("123","qwe", {"name":"test"})
    #     self.assertTrue(left.status)
    #     left_two = job.set_state("123","qwerty", {"name2":"test2"})
    #     self.assertTrue(left_two.status)
    #     left_three = job.set_state("1234", "qwerty", {"name3": "test2"})
    #     self.assertTrue(left_three.status)
    #
    #     right = job.get_state("qwe","123")
    #     self.assertTrue(right.status)
    #     right_two = job.get_state("qwerty", "123")
    #     self.assertTrue(right_two.status)
    #     right_three = job.get_state("qwerty", "1234")
    #     self.assertTrue(right_three.status)
    #
    #     self.assertEqual({"name":"test"}, right.result)
    #     self.assertEqual({"name2": "test2"}, right_two.result)
    #     self.assertEqual({"name3": "test2"}, right_three.result)



if is_test[0]:
    unittest.main()
else:
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=True)
