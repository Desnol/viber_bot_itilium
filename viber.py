import os
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.picture_message import PictureMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.keyboard_message import KeyboardMessage
from viberbot.api.messages.rich_media_message import RichMediaMessage
import requests
import logging
from flask import Flask, request, Response
import psycopg2
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from viberbot.api.viber_requests import ViberDeliveredRequest

import json

def ViberSendMessages(to, messages):
    print("stack: ViberSendMessages")
    SaveIdSendetCommand(viber.send_messages(to, messages), to)

def SaveIdSendetCommand(list_tokens, sender_id):
    print("stack: SaveIdSendetCommand")
    #Сохранить в базу отправленные команды
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_undelivered_send_messages',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_undelivered_send_messages (id serial PRIMARY KEY, sender_id varchar(50), message_id text );")
        # Pass data to fill a query placeholders and let Psycopg perform
        # the correct conversion (no more SQL injections!)
        for message_id in list_tokens:
            cur.execute("INSERT INTO data_undelivered_send_messages (sender_id, message_id) VALUES (%s, %s)",
              (sender_id, str(message_id)))

       # Make the changes to the database persistent
        conn.commit()
        # Close communication with the database
    except Exception as e:
        print("Error on SaveIdSendetCommand" + e.args[0])
    finally:
        cur.close()
        conn.close()


def ExistNotDeliveredCommands(sender_id):
    print("stack: ExistNotDeliveredCommands")
    #Есть недоставленые команды, отправленные ботом пользователю
    exist_records = False
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        need_query = True

        cur.execute("select * from information_schema.tables where table_name=%s", ('data_undelivered_send_messages',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_undelivered_send_messages (id serial PRIMARY KEY, sender_id varchar(50), message_id text );")
            need_query = False

        if need_query:
            cur.execute("select * from data_undelivered_send_messages where sender_id=%s", (sender_id,))
            if(cur.rowcount > 0):
                exist_records = True
       # Make the changes to the database persistent
        conn.commit()
        # Close communication with the database
    except Exception as e:
        print("Error on ExistNotDeliveredCommands" + e.args[0])
        return False
    finally:
        cur.close()
        conn.close()
    return exist_records


def onFailedDeliveredMessage(message_id, sender_id):
    print("stack: onFailedDeliveredMessage")
    # Ошибка при доставке команды, отправленной ботом пользователю - удалим все
    # команды, сохраненные у пользователя и перейдем на состояние ошибки
    # тут надо не зациклиться, нельзя пользователю посылать в этом состоянии
    # команды.
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        need_drop = True
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_undelivered_send_messages',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_undelivered_send_messages (id serial PRIMARY KEY, sender_id varchar(50), message_id text );")
            need_drop = False

        if need_drop:
            cur.execute("DELETE FROM data_undelivered_send_messages WHERE sender_id = %s", (sender_id, ));

       # Make the changes to the database persistent
        conn.commit()
        # Close communication with the database
    except Exception as e:
        print("Error on onFailedDeliveredMessage" + e.args[0])
    finally:
        cur.close()
        conn.close()



def onDeliveredMessage(message_id, sender_id):
    print("stack: onDeliveredMessage")
    #доставка команды пользователю - надо удалить из списка сохраненных команд
    # эту команду
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        need_drop = True
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_undelivered_send_messages',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_undelivered_send_messages (id serial PRIMARY KEY, sender_id varchar(50), message_id text );")
            need_drop = False

        if need_drop:
            cur.execute("DELETE FROM data_undelivered_send_messages WHERE sender_id = %s and message_id = %s", (sender_id, str(message_id)));

       # Make the changes to the database persistent
        conn.commit()
        # Close communication with the database
    except Exception as e:
        print("Error on onDeliveredMessage " + e.args[0])
    finally:
        cur.close()
        conn.close()



def SaveStateToPostgress(sender_id, state_id, carousel_id, data_user, data):
    print("stack: SaveStateToPostgress")
    data_user_string = json.dumps(data_user)
    data_bot_string = json.dumps(data)
    state = True
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations

        cur = conn.cursor()

        need_drop = True
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_users',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_users (id serial PRIMARY KEY, sender_id varchar(50), state_id varchar(36), carousel_id varchar(36),data_user text, data text );")
            need_drop = False

        if need_drop:
            cur.execute("DELETE FROM data_users WHERE sender_id = %s", (sender_id,));
        # Pass data to fill a query placeholders and let Psycopg perform
        # the correct conversion (no more SQL injections!)
        cur.execute("INSERT INTO data_users (sender_id, state_id, carousel_id, data_user, data) VALUES (%s, %s, %s, %s, %s)",
              (sender_id, state_id, carousel_id, data_user_string, data_bot_string))

       # Make the changes to the database persistent
        conn.commit()
        # Close communication with the database
    except:
        state = False
    finally:
        cur.close()
        conn.close()
    return state

def RestoreStateFromPostgress(sender_id):
    print("stack: RestoreStateFromPostgress")
    state = False
    is_error = False
    try:
        restore_ok = True
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()

        cur.execute("select * from information_schema.tables where table_name=%s", ('data_users',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_users (id serial PRIMARY KEY, sender_id varchar(50), state_id varchar(36), carousel_id varchar(36),data_user text, data text );")
            conn.commit()
            restore_ok = False

        if not restore_ok:
            return {'error': is_error, 'state' : False}
        cur.execute("SELECT sender_id,  state_id,  carousel_id, data_user,  data FROM data_users WHERE sender_id = %s", (sender_id,))
        result_query = cur.fetchone()
        if(not result_query == None):
            return {'state':True, 'sender_id':result_query[0], 'state_id':result_query[1], 'carousel_id':result_query[2],'data_user':json.loads(result_query[3]), 'data':json.loads(result_query[4])}
        else:
            return {'error': is_error, 'state' : False}

        # Make the changes to the database persistent

        # Close communication with the database
    except Exception as e:
        is_error = True
        restore_ok = False
        print("Error on restore data:" + e.args[0])
    finally:
        cur.close()
        conn.close()
    return {'error': is_error, 'state' : state}

address_api_itilium = os.environ['AddressApiItilium']
login_itilium = os.environ['LoginItilium']
password_itilium = os.environ['PasswordItilium']
auth_token_out = os.environ['AuthToken']

def GetTextCommand(message):
    text = ""
    print("stack: GetTextCommand")
    if (isinstance(message, str)):
        text = message
    elif (isinstance(message, TextMessage)):
        text = message.text
    elif (isinstance(message, PictureMessage)):
        text = message.media + '<ngnRy8ET67ZqpLwmWVD1JecklqI2RKO0ffpraTYdjzcpRsSvLXF7JNSotF7s>' + message.text
    else:
        text = message.text
    return text

def GetIsRegisteredUser(sender_id):
    is_error, text, state = RequestItilium({"data": {"action": "is_not_registered","sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка работы сети. Проверьте доступность сети:" + text_error))
        return False
    else:
        if state:
            if str(text) == "0":
                return True
            else:
                return False
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text="Ошибка при проверке регистрации, проверьте доступность Основной базы:" + str(text_error)))
            return False

def GetIdErrorState():
    print("stack: GetIdErrorState")
    return "095761bb-67d8-455b-bf09-4e32d0e8dc4f" #Выбор действия

def ShowCarousel(sender_id, result_list, number_parts):

    print("stack: ShowCarousel")
    max_buttons = 42
    if (len(result_list) > max_buttons ):
        count_in_part = max_buttons
        first_number = number_parts * count_in_part - count_in_part
        last_number = first_number + count_in_part - 1
        index = 0
        buttons = []
        isEnd = True
        for id_cortage, title_cortage in result_list:
            id = id_cortage
            view = title_cortage
            if (index > last_number):
                isEnd = False
                break
            elif index >= first_number:
                buttons.append({"TextVAlign": "top", "TextHAlign": "left", "ActionBody": id, "ActionType":"reply", "Text": view})
            index += 1
        buttons_keyboard = []
        if (isEnd == False):
            buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "more_data", "Text": "ЕЩЕ"})
        if (number_parts > 1 ):
            buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "back_data", "Text": "Назад"})
        buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "cancel", "Text": "Отменить"})
        text_keyboard = {"Type": "keyboard","InputFieldState": "hidden", "Buttons": buttons_keyboard}
        ViberSendMessages(sender_id, [RichMediaMessage(min_api_version=4, rich_media={"Type": "rich_media", "BgColor": "#FFFFFF",
                                                          "Buttons":buttons}), KeyboardMessage(
                                                                   keyboard=text_keyboard, min_api_version=4)])
    else:
        text_keyboard = {"Type": "keyboard", "InputFieldState": "hidden"}
        buttons = []
        buttons_keyboard = []
        for id_cortage, title_cortage  in result_list:
            id = id_cortage
            view = title_cortage
            buttons.append({"TextVAlign": "top", "TextHAlign": "left", "ActionBody": id, "Text": view})
        buttons_keyboard.append({"Columns": 6, "Rows": 1, "ActionBody": "cancel", "Text": "Отменить"})
        text_keyboard.update({"Buttons": buttons_keyboard})
        ViberSendMessages(sender_id, [RichMediaMessage(min_api_version=4, rich_media={"Type": "rich_media", "BgColor": "#FFFFFF",
                                                            "Buttons":buttons}), KeyboardMessage(
                                                                     keyboard=text_keyboard, min_api_version=4)])

def SaveState(sender_id, state_id, data, data_user, carousel_id):
    print("stack: SaveState")
    print(" state_id " + state_id)
    print(" sender_id " + sender_id)
    if SaveStateToPostgress(sender_id, state_id, carousel_id, data_user, data):
        return True
    else:
        return False

def RestoreState(sender_id):
    print("stack: RestoreState")
    result_dict = RestoreStateFromPostgress(sender_id)
    if result_dict.get('state') == True:
         return (True, False ,result_dict.get('state_id'), result_dict.get('data'), result_dict.get('data_user'), result_dict.get('carousel_id'))
    else:
         return (False,  result_dict.get('error'), "", "", "", "")




def proc02957edd8e984dd4a0aa530f15bba971(sender_id, message, data, service_data_bot_need, carousel_id):
    #Приветствие (программный выбор)
    print("stack: proc02957edd8e984dd4a0aa530f15bba971")
    if GetIdStateForClearData() == "02957edd-8e98-4dd4-a0aa-530f15bba971":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Добрый день!"))
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function02957edd8e984dd4a0aa530f15bba971(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "error":
        proc6cc30e06b21a4176892b507ee382b3e8(sender_id, message, data, service_data_bot_need, carousel_id) #Состояние ошибки при Приветствии
    elif result_programm_select == "0":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "1":
        proc1b68be2d5a9a4d06adb59b874e1673ea(sender_id, message, data, service_data_bot_need, carousel_id) #Ввод секретного кода
    return

def proc_function02957edd8e984dd4a0aa530f15bba971(sender_id, message, data, service_data_bot_need, carousel_id):
    #Приветствие (функция программного выбора)
    print("stack: proc_function02957edd8e984dd4a0aa530f15bba971")
    is_error, text, state = RequestItilium({"data": {"action": "is_not_registered","sender": sender_id}})
    if is_error:
        text_error = text
        return "error" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            if str(text) == "0":
                return "0"
            else:
                return "1"
        else:
            text_error = text
            return "error" # В процедуре обработке надо направить на нужное состояние

def proc1b68be2d5a9a4d06adb59b874e1673ea(sender_id, message, data, service_data_bot_need, carousel_id):
    #Ввод секретного кода (выбор по результатам ввода с клавиатуры)
    print("stack: proc1b68be2d5a9a4d06adb59b874e1673ea")
    if GetIdStateForClearData() == "1b68be2d-5a9a-4d06-adb5-9b874e1673ea":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Введите идентификатор подписчика"))
    if not SaveState(sender_id, "b68be2d-5a9a-4d06-adb5-9b874e1673ea1", service_data_bot_need, data, carousel_id): #proc_function_expect_user1b68be2d5a9a4d06adb59b874e1673ea
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_user1b68be2d5a9a4d06adb59b874e1673ea(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_user1b68be2d5a9a4d06adb59b874e1673ea")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    result_programm_select = proc_function1b68be2d5a9a4d06adb59b874e1673ea(sender_id, text, data, carousel_id)
    if result_programm_select == "0":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "1":
        proc2b3f0bd4eef0409c9ffb14ffb0d21861(sender_id, message, data, service_data_bot_need, carousel_id) #Секретный код неверный
    elif result_programm_select == "error":
        proc1b68be2d5a9a4d06adb59b874e1673ea(sender_id, message, data, service_data_bot_need, carousel_id) #Ввод секретного кода

def proc_function1b68be2d5a9a4d06adb59b874e1673ea(sender_id, text, data, carousel_id):
    #Ввод секретного кода (функция обработки выбора с клавиатуры)
    print("stack: proc_function1b68be2d5a9a4d06adb59b874e1673ea")
    is_error, text, state = RequestItilium({"data": {"action": "is_valid_code", "phone":text,"sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            if str(text) == "1":
                return "0"
            else:
                ViberSendMessages(sender_id, TextMessage(text=text))
                return "1"
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text="error with code:" + str(text_error)))
            return "error" # В процедуре обработке надо направить на нужное состояние

def proc2b3f0bd4eef0409c9ffb14ffb0d21861(sender_id, message, data, service_data_bot_need, carousel_id):
    #Секретный код неверный
    print("stack: proc2b3f0bd4eef0409c9ffb14ffb0d21861")
    if GetIdStateForClearData() == "2b3f0bd4-eef0-409c-9ffb-14ffb0d21861":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Секретный код неверный!"))
    proc1b68be2d5a9a4d06adb59b874e1673ea(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Ввод секретного кода
    return

def proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id):
    #Выбор действия (выбор из подчиненных команд)
    print("stack: proc095761bb67d8455bbf094e32d0e8dc4f")
    if GetIdStateForClearData() == "095761bb-67d8-455b-bf09-4e32d0e8dc4f":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "095761bb-67d8-455b-bf09-4e32d0e8dc4f", service_data_bot_need, data, carousel_id): #proc095761bb67d8455bbf094e32d0e8dc4f
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    ViberSendMessages(sender_id, TextMessage(text="Выберите действие"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "76456fc5-a5d3-4b54-81dc-b15c34787790",
        "Text": "Зарегистрировать обращение" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "91d863c1-0ff0-456b-acb0-86818cac8a03",
        "Text": "Внести уточнения" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "5160f46d-71b8-466a-8b28-db1bf17d5392",
        "Text": "Обращения для подтверждения" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "cdab1713-d317-452b-bbdb-8a484d513051",
        "Text": "Последние сообщения" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "f6829c8b-eb46-4c61-8ab6-3bd31f6bc879",
        "Text": "Получить статус" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "95761bb-67d8-455b-bf09-4e32d0e8dc4f0", service_data_bot_need, data, carousel_id): #proc_expect_user_button_click095761bb67d8455bbf094e32d0e8dc4f
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_click095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id):
    #Выбор действия (Обработчик выбора из подчиненных команд)
    print("stack: proc_expect_user_button_click095761bb67d8455bbf094e32d0e8dc4f")
    command = GetTextCommand(message)
    if command == "76456fc5-a5d3-4b54-81dc-b15c34787790":
        proc76456fc5a5d34b5481dcb15c34787790(sender_id, message, data, service_data_bot_need, carousel_id) #Зарегистрировать обращение
    elif command == "91d863c1-0ff0-456b-acb0-86818cac8a03":
        proc91d863c10ff0456bacb086818cac8a03(sender_id, message, data, service_data_bot_need, carousel_id) #Внести уточнения
    elif command == "5160f46d-71b8-466a-8b28-db1bf17d5392":
        proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id) #Обращения для подтверждения
    elif command == "cdab1713-d317-452b-bbdb-8a484d513051":
        proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Последние сообщения
    elif command == "f6829c8b-eb46-4c61-8ab6-3bd31f6bc879":
        procf6829c8beb464c618ab63bd31f6bc879(sender_id, message, data, service_data_bot_need, carousel_id) #Получить статус
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc76456fc5a5d34b5481dcb15c34787790(sender_id, message, data, service_data_bot_need, carousel_id):
    #Зарегистрировать обращение (выбор по результатам ввода с клавиатуры)
    print("stack: proc76456fc5a5d34b5481dcb15c34787790")
    if GetIdStateForClearData() == "76456fc5-a5d3-4b54-81dc-b15c34787790":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Опишите вашу проблему."))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "6cc42644-4b07-4aa8-88dc-eecf90f5260a",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "regular", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "6456fc5-a5d3-4b54-81dc-b15c347877907", service_data_bot_need, data, carousel_id): #proc_function_expect_user76456fc5a5d34b5481dcb15c34787790
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_user76456fc5a5d34b5481dcb15c34787790(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_user76456fc5a5d34b5481dcb15c34787790")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    if text == "6cc42644-4b07-4aa8-88dc-eecf90f5260a":
        proc6cc426444b074aa888dceecf90f5260a(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Отмена
        return
    result_programm_select = proc_function76456fc5a5d34b5481dcb15c34787790(sender_id, text, data, carousel_id)
    if result_programm_select == "error_network":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "error_in_itilium":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "OK":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc_function76456fc5a5d34b5481dcb15c34787790(sender_id, text, data, carousel_id):
    #Зарегистрировать обращение (функция обработки выбора с клавиатуры)
    print("stack: proc_function76456fc5a5d34b5481dcb15c34787790")
    is_error, text, state = RequestItilium({"data": {"action": "is_registration","text": text, "sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            ViberSendMessages(sender_id, TextMessage(text=str("Зарегистрирован документ:" + str(text))))
            return "OK" # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proc6cc426444b074aa888dceecf90f5260a(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отмена
    print("stack: proc6cc426444b074aa888dceecf90f5260a")
    if GetIdStateForClearData() == "6cc42644-4b07-4aa8-88dc-eecf90f5260a":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Обращение не зарегистрировано"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proc91d863c10ff0456bacb086818cac8a03(sender_id, message, data, service_data_bot_need, carousel_id):
    #Внести уточнения (программный выбор)
    print("stack: proc91d863c10ff0456bacb086818cac8a03")
    if GetIdStateForClearData() == "91d863c1-0ff0-456b-acb0-86818cac8a03":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function91d863c10ff0456bacb086818cac8a03(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "error_network":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "error_in_itilium":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "OK":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_programm_select == "confirm_incidents_carousel":
        proc1252095275704b2a907cb2e089e0ed77(sender_id, message, data, service_data_bot_need, carousel_id) #Карусель внести уточнения
    elif result_programm_select == "comand_to_selected_incident":
        proc4cca60de6e5643a0a27b251f132fafac(sender_id, message, data, service_data_bot_need, carousel_id) #Команды для выбранного инцидента для уточнения
    return

def proc_function91d863c10ff0456bacb086818cac8a03(sender_id, message, data, service_data_bot_need, carousel_id):
    #Внести уточнения (функция программного выбора)
    print("stack: proc_function91d863c10ff0456bacb086818cac8a03")
    is_error, text, state = RequestItilium({"data": {"action": "is_list_open_incidents","sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            list = json.loads(text)
            if len(list) == 0:
                ViberSendMessages(sender_id, TextMessage(text="У вас нет зарегистрированных открытых обращений"))
                return "OK"
            elif len(list) == 1:
                ViberSendMessages(sender_id, TextMessage(text=list[0].get('detail_view')))
                carousel_id = list[0].get('id')
                return "comand_to_selected_incident"
            else:
                list_ret = []
                list_ret_full = []
                for incident in list:
                    list_ret.append((incident.get('id'),incident.get('view')))
                    list_ret_full.append((incident.get('id'),incident.get('detail_view')))
                data.update({'list_open_incidents_full':list_ret_full, "list_open_incidents": list_ret})
                return "confirm_incidents_carousel"
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proc1252095275704b2a907cb2e089e0ed77(sender_id, message, data, service_data_bot_need, carousel_id):
    #Карусель внести уточнения (Карусель)
    print("stack: proc1252095275704b2a907cb2e089e0ed77")
    if GetIdStateForClearData() == "12520952-7570-4b2a-907c-b2e089e0ed77":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "12520952-7570-4b2a-907c-b2e089e0ed77", service_data_bot_need, data, carousel_id): #proc1252095275704b2a907cb2e089e0ed77
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return

    number_parts = 1;
    temp = service_data_bot_need.get("number_parts1252095275704b2a907cb2e089e0ed77")
    if not temp == None:
        number_parts = temp
    result_list = proc_get_list_corteges1252095275704b2a907cb2e089e0ed77(sender_id, data, carousel_id)
    if isinstance(result_list, list):

        ShowCarousel(sender_id, result_list, number_parts)
        service_data_bot_need.update({"number_parts1252095275704b2a907cb2e089e0ed77":number_parts})
        if not SaveState(sender_id, "2520952-7570-4b2a-907c-b2e089e0ed771", service_data_bot_need, data, carousel_id): #proc_expect_comand_user1252095275704b2a907cb2e089e0ed77
            ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
            GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
            return
    return

def proc_get_list_corteges1252095275704b2a907cb2e089e0ed77(sender_id, data, carousel_id):
    #Карусель внести уточнения (получение списка кортежей)
    print("stack: proc_get_list_corteges1252095275704b2a907cb2e089e0ed77")
    return data.get('list_open_incidents')


def proc_expect_comand_user1252095275704b2a907cb2e089e0ed77(sender_id, message, data, service_data_bot_need, carousel_id):
    #Карусель внести уточнения (обработчик выбора пользователя из карусели или команды под ней)
    print("stack: proc_expect_comand_user1252095275704b2a907cb2e089e0ed77")
    id = GetTextCommand(message)
    if id == "cancel":
        proca0981bccc8ee486e943257b9de36f2d1(sender_id, message, data, service_data_bot_need, carousel_id) #Уточнения не внесены(команда "Отменить")
    elif id == "more_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_parts1252095275704b2a907cb2e089e0ed77")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_parts1252095275704b2a907cb2e089e0ed77": number_parts + 1})
        proc1252095275704b2a907cb2e089e0ed77(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод дополнительных непоместившихся элементов
    elif id == "back_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_parts1252095275704b2a907cb2e089e0ed77")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_parts1252095275704b2a907cb2e089e0ed77": number_parts - 1})
        proc1252095275704b2a907cb2e089e0ed77(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод предыдущих элементов
    else:
        carousel_id = id
        proc84c5c09c78824f2f819bd1eef1b3913e(sender_id, message, data, service_data_bot_need, carousel_id) #Обработчик вывода (Вывод элемента карусели)
        proced689fd18d5942468b1892b7a2f97292(sender_id, message, data, service_data_bot_need, carousel_id) #Команды карусели (Вывод команд для выбранного элемента карусели)
    return

def proc84c5c09c78824f2f819bd1eef1b3913e(sender_id, message, data, service_data_bot_need, carousel_id):
    #Обработчик вывода
    print("stack: proc84c5c09c78824f2f819bd1eef1b3913e")
    if GetIdStateForClearData() == "84c5c09c-7882-4f2f-819b-d1eef1b3913e":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Выбранное обращение"))

    detail_view = proc_get_user_detail_view_by_id84c5c09c78824f2f819bd1eef1b3913e(sender_id, carousel_id, data)
    ViberSendMessages(sender_id, TextMessage(text=detail_view))
    return

def proc_get_user_detail_view_by_id84c5c09c78824f2f819bd1eef1b3913e(sender_id, carousel_id, data):
    #Обработчик вывода (функция получения детального представления выбранного элемента карусели)
    print("stack: proc_get_user_detail_view_by_id84c5c09c78824f2f819bd1eef1b3913e")
    for id, detail_view in data.get('list_open_incidents_full'):
        if id == carousel_id:
            return detail_view
    return "Не найден"

def proced689fd18d5942468b1892b7a2f97292(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды карусели (команды элемента карусели)
    print("stack: proced689fd18d5942468b1892b7a2f97292")
    if GetIdStateForClearData() == "ed689fd1-8d59-4246-8b18-92b7a2f97292":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "ed689fd1-8d59-4246-8b18-92b7a2f97292", service_data_bot_need, data, carousel_id): #proced689fd18d5942468b1892b7a2f97292
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "bb53668e-eb8e-4153-bdf7-a72781739830",
        "Text": "Ввести уточнение" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "2ad315bd-42ff-45b8-85ae-cdc9d04c0a9e",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons":buttons}))
    if not SaveState(sender_id, "d689fd1-8d59-4246-8b18-92b7a2f97292e", service_data_bot_need, data, carousel_id): #proc_expect_user_button_clicked689fd18d5942468b1892b7a2f97292
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_clicked689fd18d5942468b1892b7a2f97292(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды карусели (Обработчик выбора из подчиненных команд элемента карусели)
    print("stack: proc_expect_user_button_clicked689fd18d5942468b1892b7a2f97292")
    command = GetTextCommand(message)
    if command == "bb53668e-eb8e-4153-bdf7-a72781739830":
        procbb53668eeb8e4153bdf7a72781739830(sender_id, message, data, service_data_bot_need, carousel_id) #Ввести уточнение
    elif command == "2ad315bd-42ff-45b8-85ae-cdc9d04c0a9e":
        proc2ad315bd42ff45b885aecdc9d04c0a9e(sender_id, message, data, service_data_bot_need, carousel_id) #Отмена
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def procbb53668eeb8e4153bdf7a72781739830(sender_id, message, data, service_data_bot_need, carousel_id):
    #Ввести уточнение (выбор по результатам ввода с клавиатуры)
    print("stack: procbb53668eeb8e4153bdf7a72781739830")
    if GetIdStateForClearData() == "bb53668e-eb8e-4153-bdf7-a72781739830":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Укажите текст"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "29615d83-6647-459d-ac36-095a2b7287cc",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "regular", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "b53668e-eb8e-4153-bdf7-a72781739830b", service_data_bot_need, data, carousel_id): #proc_function_expect_userbb53668eeb8e4153bdf7a72781739830
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_userbb53668eeb8e4153bdf7a72781739830(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_userbb53668eeb8e4153bdf7a72781739830")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    if text == "29615d83-6647-459d-ac36-095a2b7287cc":
        proc29615d836647459dac36095a2b7287cc(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Отмена
        return
    result_programm_select = proc_functionbb53668eeb8e4153bdf7a72781739830(sender_id, text, data, carousel_id)
    if result_programm_select == "OK":
        proce022f99d4b914e8a8469546d143ff4e5(sender_id, message, data, service_data_bot_need, carousel_id) #Уточнения внесены
    elif result_programm_select == "error_network":
        proca0981bccc8ee486e943257b9de36f2d1(sender_id, message, data, service_data_bot_need, carousel_id) #Уточнения не внесены
    elif result_programm_select == "error_in_itilium":
        proca0981bccc8ee486e943257b9de36f2d1(sender_id, message, data, service_data_bot_need, carousel_id) #Уточнения не внесены

def proc_functionbb53668eeb8e4153bdf7a72781739830(sender_id, text, data, carousel_id):
    #Ввести уточнение (функция обработки выбора с клавиатуры)
    print("stack: proc_functionbb53668eeb8e4153bdf7a72781739830")
    is_error, text, state = RequestItilium({"data": {"action": "is_add_converstaion","incident" : carousel_id,"text":text,"sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            return "OK" # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proc2ad315bd42ff45b885aecdc9d04c0a9e(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отмена
    print("stack: proc2ad315bd42ff45b885aecdc9d04c0a9e")
    if GetIdStateForClearData() == "2ad315bd-42ff-45b8-85ae-cdc9d04c0a9e":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proca0981bccc8ee486e943257b9de36f2d1(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Уточнения не внесены
    return

def proca0981bccc8ee486e943257b9de36f2d1(sender_id, message, data, service_data_bot_need, carousel_id):
    #Уточнения не внесены
    print("stack: proca0981bccc8ee486e943257b9de36f2d1")
    if GetIdStateForClearData() == "a0981bcc-c8ee-486e-9432-57b9de36f2d1":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Уточнения не внесены"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proce022f99d4b914e8a8469546d143ff4e5(sender_id, message, data, service_data_bot_need, carousel_id):
    #Уточнения внесены
    print("stack: proce022f99d4b914e8a8469546d143ff4e5")
    if GetIdStateForClearData() == "e022f99d-4b91-4e8a-8469-546d143ff4e5":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Уточнения внесены"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proc4cca60de6e5643a0a27b251f132fafac(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды для выбранного инцидента для уточнения (выбор из подчиненных команд)
    print("stack: proc4cca60de6e5643a0a27b251f132fafac")
    if GetIdStateForClearData() == "4cca60de-6e56-43a0-a27b-251f132fafac":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "4cca60de-6e56-43a0-a27b-251f132fafac", service_data_bot_need, data, carousel_id): #proc4cca60de6e5643a0a27b251f132fafac
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "971494b8-473d-4fbe-94c6-86b320392d3a",
        "Text": "Введите уточнение" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "29615d83-6647-459d-ac36-095a2b7287cc",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "cca60de-6e56-43a0-a27b-251f132fafac4", service_data_bot_need, data, carousel_id): #proc_expect_user_button_click4cca60de6e5643a0a27b251f132fafac
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_click4cca60de6e5643a0a27b251f132fafac(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды для выбранного инцидента для уточнения (Обработчик выбора из подчиненных команд)
    print("stack: proc_expect_user_button_click4cca60de6e5643a0a27b251f132fafac")
    command = GetTextCommand(message)
    if command == "971494b8-473d-4fbe-94c6-86b320392d3a":
        proc971494b8473d4fbe94c686b320392d3a(sender_id, message, data, service_data_bot_need, carousel_id) #Введите уточнение
    elif command == "29615d83-6647-459d-ac36-095a2b7287cc":
        proc29615d836647459dac36095a2b7287cc(sender_id, message, data, service_data_bot_need, carousel_id) #Отмена
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc971494b8473d4fbe94c686b320392d3a(sender_id, message, data, service_data_bot_need, carousel_id):
    #Введите уточнение
    print("stack: proc971494b8473d4fbe94c686b320392d3a")
    if GetIdStateForClearData() == "971494b8-473d-4fbe-94c6-86b320392d3a":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    procbb53668eeb8e4153bdf7a72781739830(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Введите уточнение
    return

def proc29615d836647459dac36095a2b7287cc(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отмена
    print("stack: proc29615d836647459dac36095a2b7287cc")
    if GetIdStateForClearData() == "29615d83-6647-459d-ac36-095a2b7287cc":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc2ad315bd42ff45b885aecdc9d04c0a9e(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Отмена
    return

def proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id):
    #Обращения для подтверждения (Карусель)
    print("stack: proc5160f46d71b8466a8b28db1bf17d5392")
    if GetIdStateForClearData() == "5160f46d-71b8-466a-8b28-db1bf17d5392":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "5160f46d-71b8-466a-8b28-db1bf17d5392", service_data_bot_need, data, carousel_id): #proc5160f46d71b8466a8b28db1bf17d5392
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    ViberSendMessages(sender_id, TextMessage(text="Обращения для подтверждения"))

    number_parts = 1;
    temp = service_data_bot_need.get("number_parts5160f46d71b8466a8b28db1bf17d5392")
    if not temp == None:
        number_parts = temp
    result_list = proc_get_list_corteges5160f46d71b8466a8b28db1bf17d5392(sender_id, data, carousel_id)
    if isinstance(result_list, list):

        ShowCarousel(sender_id, result_list, number_parts)
        service_data_bot_need.update({"number_parts5160f46d71b8466a8b28db1bf17d5392":number_parts})
        if not SaveState(sender_id, "160f46d-71b8-466a-8b28-db1bf17d53925", service_data_bot_need, data, carousel_id): #proc_expect_comand_user5160f46d71b8466a8b28db1bf17d5392
            ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
            GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
            return
    elif result_list == "error_network":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_list == "error_in_itilium":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_list == "no_data":
        procff766d22eecd4b8a9509ad556751429f(sender_id, message, data, service_data_bot_need, carousel_id) #Нет обращений
    return

def proc_get_list_corteges5160f46d71b8466a8b28db1bf17d5392(sender_id, data, carousel_id):
    #Обращения для подтверждения (получение списка кортежей)
    print("stack: proc_get_list_corteges5160f46d71b8466a8b28db1bf17d5392")
    is_error, text, state = RequestItilium({"data": {"action": "is_list_need_confirmed_incidents","sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            # data.update({'detail_text':text})
            list = json.loads(text)
            if len(list) == 0:
                return "no_data"
            list_ret = []
            list_ret_full = []
            for incident in list:
                list_ret.append((incident.get('id'),incident.get('view')))
                list_ret_full.append((incident.get('id'),incident.get('detail_view')))
            data.update({'list_open_incidents':list_ret_full})
            return list_ret # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние


def proc_expect_comand_user5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id):
    #Обращения для подтверждения (обработчик выбора пользователя из карусели или команды под ней)
    print("stack: proc_expect_comand_user5160f46d71b8466a8b28db1bf17d5392")
    id = GetTextCommand(message)
    if id == "cancel":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия(команда "Отменить")
    elif id == "more_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_parts5160f46d71b8466a8b28db1bf17d5392")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_parts5160f46d71b8466a8b28db1bf17d5392": number_parts + 1})
        proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод дополнительных непоместившихся элементов
    elif id == "back_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_parts5160f46d71b8466a8b28db1bf17d5392")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_parts5160f46d71b8466a8b28db1bf17d5392": number_parts - 1})
        proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод предыдущих элементов
    else:
        carousel_id = id
        procdbb86b04001b4aa587bd0598114130e3(sender_id, message, data, service_data_bot_need, carousel_id) #Вывод элемента карусели (Вывод элемента карусели)
        procdae1f3640d8a4eb0aed3fc1b63e187aa(sender_id, message, data, service_data_bot_need, carousel_id) #Команды карусели (Вывод команд для выбранного элемента карусели)
    return

def procdae1f3640d8a4eb0aed3fc1b63e187aa(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды карусели (команды элемента карусели)
    print("stack: procdae1f3640d8a4eb0aed3fc1b63e187aa")
    if GetIdStateForClearData() == "dae1f364-0d8a-4eb0-aed3-fc1b63e187aa":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "dae1f364-0d8a-4eb0-aed3-fc1b63e187aa", service_data_bot_need, data, carousel_id): #procdae1f3640d8a4eb0aed3fc1b63e187aa
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "5ba6c9fd-cb21-4aa2-972c-4020574f3157",
        "Text": "Подтвердить" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "3ec26f31-a5dd-4ff7-a95f-c7c612cf273a",
        "Text": "Отклонить" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "42747c5a-b756-49b0-b830-bcf82d3dca9c",
        "Text": "Назад" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons":buttons}))
    if not SaveState(sender_id, "ae1f364-0d8a-4eb0-aed3-fc1b63e187aad", service_data_bot_need, data, carousel_id): #proc_expect_user_button_clickdae1f3640d8a4eb0aed3fc1b63e187aa
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_clickdae1f3640d8a4eb0aed3fc1b63e187aa(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды карусели (Обработчик выбора из подчиненных команд элемента карусели)
    print("stack: proc_expect_user_button_clickdae1f3640d8a4eb0aed3fc1b63e187aa")
    command = GetTextCommand(message)
    if command == "5ba6c9fd-cb21-4aa2-972c-4020574f3157":
        proc5ba6c9fdcb214aa2972c4020574f3157(sender_id, message, data, service_data_bot_need, carousel_id) #Подтвердить
    elif command == "3ec26f31-a5dd-4ff7-a95f-c7c612cf273a":
        proc3ec26f31a5dd4ff7a95fc7c612cf273a(sender_id, message, data, service_data_bot_need, carousel_id) #Отклонить
    elif command == "42747c5a-b756-49b0-b830-bcf82d3dca9c":
        proc42747c5ab75649b0b830bcf82d3dca9c(sender_id, message, data, service_data_bot_need, carousel_id) #Назад
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc5ba6c9fdcb214aa2972c4020574f3157(sender_id, message, data, service_data_bot_need, carousel_id):
    #Подтвердить (программный выбор)
    print("stack: proc5ba6c9fdcb214aa2972c4020574f3157")
    if GetIdStateForClearData() == "5ba6c9fd-cb21-4aa2-972c-4020574f3157":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function5ba6c9fdcb214aa2972c4020574f3157(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "need_rating":
        proca22a380f1e104600808c465bd6ab3777(sender_id, message, data, service_data_bot_need, carousel_id) #Указать оценку обязательно
    elif result_programm_select == "rating_exist":
        procd454043806d1401f87b5ab49f4142f18(sender_id, message, data, service_data_bot_need, carousel_id) #Указать оценку по желанию
    elif result_programm_select == "error_network":
        proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id) #Обращение не подтверждено
    elif result_programm_select == "error_in_itilium":
        proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id) #Обращение не подтверждено
    elif result_programm_select == "confirm":
        proc01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id) #Подтвердить общая
    return

def proc_function5ba6c9fdcb214aa2972c4020574f3157(sender_id, message, data, service_data_bot_need, carousel_id):
    #Подтвердить (функция программного выбора)
    print("stack: proc_function5ba6c9fdcb214aa2972c4020574f3157")
    is_error, text, state = RequestItilium({"data": {"action": "is_get_rating_for_incidents_confirmation", "incident":carousel_id,"sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            dictionary = json.loads(text)
            five_need_comment = dictionary.get('five_need_comment')
            four_need_comment = dictionary.get('four_need_comment')
            three_need_comment = dictionary.get('three_need_comment')
            two_need_comment = dictionary.get('two_need_comment')
            one_need_comment = dictionary.get('one_need_comment')
            need_rating = dictionary.get('need_rating')
            rating_exist = dictionary.get('rating_exist')
            data.update(dictionary)
            if need_rating:
                return "need_rating"
            elif rating_exist:
                return "rating_exist"
            else:
                data.update({"rating":-1, "comment": ""})
                return "confirm"
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proca22a380f1e104600808c465bd6ab3777(sender_id, message, data, service_data_bot_need, carousel_id):
    #Указать оценку обязательно (выбор из подчиненных команд)
    print("stack: proca22a380f1e104600808c465bd6ab3777")
    if GetIdStateForClearData() == "a22a380f-1e10-4600-808c-465bd6ab3777":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "a22a380f-1e10-4600-808c-465bd6ab3777", service_data_bot_need, data, carousel_id): #proca22a380f1e104600808c465bd6ab3777
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    ViberSendMessages(sender_id, TextMessage(text="Оцените выполнение обращения"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "f78d8071-4386-4b3f-8cd2-91a0d503f281",
        "Text": "1" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "70a014c3-ff72-418a-bb1b-94326c535cd6",
        "Text": "2" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "1c315c3c-887a-489b-9552-2e1316af7b35",
        "Text": "3" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "12a983c4-1023-40aa-85d7-d182b9a7e2c5",
        "Text": "4" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "619fd5ff-8484-46fd-8f22-17bb68bc6a3b",
        "Text": "5" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "e6d53aa2-210b-4ed3-8e9f-5e6cea9bc777",
        "Text": "Отменить" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "22a380f-1e10-4600-808c-465bd6ab3777a", service_data_bot_need, data, carousel_id): #proc_expect_user_button_clicka22a380f1e104600808c465bd6ab3777
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_clicka22a380f1e104600808c465bd6ab3777(sender_id, message, data, service_data_bot_need, carousel_id):
    #Указать оценку обязательно (Обработчик выбора из подчиненных команд)
    print("stack: proc_expect_user_button_clicka22a380f1e104600808c465bd6ab3777")
    command = GetTextCommand(message)
    if command == "f78d8071-4386-4b3f-8cd2-91a0d503f281":
        procf78d807143864b3f8cd291a0d503f281(sender_id, message, data, service_data_bot_need, carousel_id) #1
    elif command == "70a014c3-ff72-418a-bb1b-94326c535cd6":
        proc70a014c3ff72418abb1b94326c535cd6(sender_id, message, data, service_data_bot_need, carousel_id) #2
    elif command == "1c315c3c-887a-489b-9552-2e1316af7b35":
        proc1c315c3c887a489b95522e1316af7b35(sender_id, message, data, service_data_bot_need, carousel_id) #3
    elif command == "12a983c4-1023-40aa-85d7-d182b9a7e2c5":
        proc12a983c4102340aa85d7d182b9a7e2c5(sender_id, message, data, service_data_bot_need, carousel_id) #4
    elif command == "619fd5ff-8484-46fd-8f22-17bb68bc6a3b":
        proc619fd5ff848446fd8f2217bb68bc6a3b(sender_id, message, data, service_data_bot_need, carousel_id) #5
    elif command == "e6d53aa2-210b-4ed3-8e9f-5e6cea9bc777":
        proce6d53aa2210b4ed38e9f5e6cea9bc777(sender_id, message, data, service_data_bot_need, carousel_id) #Отменить
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def procf78d807143864b3f8cd291a0d503f281(sender_id, message, data, service_data_bot_need, carousel_id):
    #1 (программный выбор)
    print("stack: procf78d807143864b3f8cd291a0d503f281")
    if GetIdStateForClearData() == "f78d8071-4386-4b3f-8cd2-91a0d503f281":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_functionf78d807143864b3f8cd291a0d503f281(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "need_comment_surely":
        procd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий обязательно
    elif result_programm_select == "need_comment":
        proc4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий необязательно
    return

def proc_functionf78d807143864b3f8cd291a0d503f281(sender_id, message, data, service_data_bot_need, carousel_id):
    #1 (функция программного выбора)
    print("stack: proc_functionf78d807143864b3f8cd291a0d503f281")
    data.update({"rating":1})
    if data.get('one_need_comment'):
        return "need_comment_surely"
    else:
        return "need_comment"

def procd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id):
    #Указать комментарий обязательно (выбор по результатам ввода с клавиатуры)
    print("stack: procd2aeca9275214a6caa98de3001dd081f")
    if GetIdStateForClearData() == "d2aeca92-7521-4a6c-aa98-de3001dd081f":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Укажите комментарий"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "7e43a768-6c96-4691-abb1-6ccf4e47e119",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "regular", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "2aeca92-7521-4a6c-aa98-de3001dd081fd", service_data_bot_need, data, carousel_id): #proc_function_expect_userd2aeca9275214a6caa98de3001dd081f
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_userd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_userd2aeca9275214a6caa98de3001dd081f")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    if text == "7e43a768-6c96-4691-abb1-6ccf4e47e119":
        proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Отмена
        return
    result_programm_select = proc_functiond2aeca9275214a6caa98de3001dd081f(sender_id, text, data, carousel_id)
    if result_programm_select == "save":
        proc01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id) #Подтвердить общая

def proc_functiond2aeca9275214a6caa98de3001dd081f(sender_id, text, data, carousel_id):
    #Указать комментарий обязательно (функция обработки выбора с клавиатуры)
    print("stack: proc_functiond2aeca9275214a6caa98de3001dd081f")
    data.update({"comment": text})
    return "save"

def proc4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id):
    #Указать комментарий необязательно (выбор по результатам ввода с клавиатуры)
    print("stack: proc4f2c3d625e2f4665bf75177d4363273c")
    if GetIdStateForClearData() == "4f2c3d62-5e2f-4665-bf75-177d4363273c":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Укажите комментарий"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "f8baff8b-ac01-4776-849f-f22db27006da",
        "Text": "Пропустить" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "regular", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "f2c3d62-5e2f-4665-bf75-177d4363273c4", service_data_bot_need, data, carousel_id): #proc_function_expect_user4f2c3d625e2f4665bf75177d4363273c
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_user4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_user4f2c3d625e2f4665bf75177d4363273c")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    if text == "f8baff8b-ac01-4776-849f-f22db27006da":
        procf8baff8bac014776849ff22db27006da(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Пропустить
        return
    result_programm_select = proc_function4f2c3d625e2f4665bf75177d4363273c(sender_id, text, data, carousel_id)
    if result_programm_select == "save":
        proc01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id) #Подтвердить общая

def proc_function4f2c3d625e2f4665bf75177d4363273c(sender_id, text, data, carousel_id):
    #Указать комментарий необязательно (функция обработки выбора с клавиатуры)
    print("stack: proc_function4f2c3d625e2f4665bf75177d4363273c")
    data.update({"comment": text})
    return "save"

def procf8baff8bac014776849ff22db27006da(sender_id, message, data, service_data_bot_need, carousel_id):
    #Пропустить
    print("stack: procf8baff8bac014776849ff22db27006da")
    if GetIdStateForClearData() == "f8baff8b-ac01-4776-849f-f22db27006da":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Подтвердить общая
    return

def proc70a014c3ff72418abb1b94326c535cd6(sender_id, message, data, service_data_bot_need, carousel_id):
    #2 (программный выбор)
    print("stack: proc70a014c3ff72418abb1b94326c535cd6")
    if GetIdStateForClearData() == "70a014c3-ff72-418a-bb1b-94326c535cd6":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function70a014c3ff72418abb1b94326c535cd6(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "need_comment_surely":
        procd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий обязательно
    elif result_programm_select == "need_comment":
        proc4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий необязательно
    return

def proc_function70a014c3ff72418abb1b94326c535cd6(sender_id, message, data, service_data_bot_need, carousel_id):
    #2 (функция программного выбора)
    print("stack: proc_function70a014c3ff72418abb1b94326c535cd6")
    data.update({"rating":2})
    if data.get('two_need_comment'):
        return "need_comment_surely"
    else:
        return "need_comment"

def proc1c315c3c887a489b95522e1316af7b35(sender_id, message, data, service_data_bot_need, carousel_id):
    #3 (программный выбор)
    print("stack: proc1c315c3c887a489b95522e1316af7b35")
    if GetIdStateForClearData() == "1c315c3c-887a-489b-9552-2e1316af7b35":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function1c315c3c887a489b95522e1316af7b35(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "need_comment_surely":
        procd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий обязательно
    elif result_programm_select == "need_comment":
        proc4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий необязательно
    return

def proc_function1c315c3c887a489b95522e1316af7b35(sender_id, message, data, service_data_bot_need, carousel_id):
    #3 (функция программного выбора)
    print("stack: proc_function1c315c3c887a489b95522e1316af7b35")
    data.update({"rating":3})
    if data.get('three_need_comment'):
        return "need_comment_surely"
    else:
        return "need_comment"

def proc12a983c4102340aa85d7d182b9a7e2c5(sender_id, message, data, service_data_bot_need, carousel_id):
    #4 (программный выбор)
    print("stack: proc12a983c4102340aa85d7d182b9a7e2c5")
    if GetIdStateForClearData() == "12a983c4-1023-40aa-85d7-d182b9a7e2c5":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function12a983c4102340aa85d7d182b9a7e2c5(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "need_comment_surely":
        procd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий обязательно
    elif result_programm_select == "need_comment":
        proc4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий необязательно
    return

def proc_function12a983c4102340aa85d7d182b9a7e2c5(sender_id, message, data, service_data_bot_need, carousel_id):
    #4 (функция программного выбора)
    print("stack: proc_function12a983c4102340aa85d7d182b9a7e2c5")
    data.update({"rating":4})
    if data.get('four_need_comment'):
        return "need_comment_surely"
    else:
        return "need_comment"

def proc619fd5ff848446fd8f2217bb68bc6a3b(sender_id, message, data, service_data_bot_need, carousel_id):
    #5 (программный выбор)
    print("stack: proc619fd5ff848446fd8f2217bb68bc6a3b")
    if GetIdStateForClearData() == "619fd5ff-8484-46fd-8f22-17bb68bc6a3b":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function619fd5ff848446fd8f2217bb68bc6a3b(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "need_comment_surely":
        procd2aeca9275214a6caa98de3001dd081f(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий обязательно
    elif result_programm_select == "need_comment":
        proc4f2c3d625e2f4665bf75177d4363273c(sender_id, message, data, service_data_bot_need, carousel_id) #Указать комментарий необязательно
    return

def proc_function619fd5ff848446fd8f2217bb68bc6a3b(sender_id, message, data, service_data_bot_need, carousel_id):
    #5 (функция программного выбора)
    print("stack: proc_function619fd5ff848446fd8f2217bb68bc6a3b")
    data.update({"rating":5})
    if data.get('five_need_comment'):
        return "need_comment_surely"
    else:
        return "need_comment"

def proce6d53aa2210b4ed38e9f5e6cea9bc777(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отменить
    print("stack: proce6d53aa2210b4ed38e9f5e6cea9bc777")
    if GetIdStateForClearData() == "e6d53aa2-210b-4ed3-8e9f-5e6cea9bc777":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Подтверждение не выполнено"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def procd454043806d1401f87b5ab49f4142f18(sender_id, message, data, service_data_bot_need, carousel_id):
    #Указать оценку по желанию (выбор из подчиненных команд)
    print("stack: procd454043806d1401f87b5ab49f4142f18")
    if GetIdStateForClearData() == "d4540438-06d1-401f-87b5-ab49f4142f18":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "d4540438-06d1-401f-87b5-ab49f4142f18", service_data_bot_need, data, carousel_id): #procd454043806d1401f87b5ab49f4142f18
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    ViberSendMessages(sender_id, TextMessage(text="Оцените выполнение обращения"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "8fe80170-3cea-47eb-8291-e37e9d4751aa",
        "Text": "1" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "15a311c3-a872-416e-a2f4-9b8f41712bad",
        "Text": "2" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "b63c3343-a6f0-42f9-bd5f-575fdbe43d20",
        "Text": "3" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "8ce4471c-310e-49c4-bad6-2b82996d23e8",
        "Text": "4" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "ea302a5c-ac3d-477b-8fd2-68a66fb56264",
        "Text": "5" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "45188a2f-e76f-463d-a930-4c5a53876d70",
        "Text": "Пропустить" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "c937a519-2897-450e-bc6b-ca9aa2c743e2",
        "Text": "Отменить" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "4540438-06d1-401f-87b5-ab49f4142f18d", service_data_bot_need, data, carousel_id): #proc_expect_user_button_clickd454043806d1401f87b5ab49f4142f18
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_clickd454043806d1401f87b5ab49f4142f18(sender_id, message, data, service_data_bot_need, carousel_id):
    #Указать оценку по желанию (Обработчик выбора из подчиненных команд)
    print("stack: proc_expect_user_button_clickd454043806d1401f87b5ab49f4142f18")
    command = GetTextCommand(message)
    if command == "8fe80170-3cea-47eb-8291-e37e9d4751aa":
        proc8fe801703cea47eb8291e37e9d4751aa(sender_id, message, data, service_data_bot_need, carousel_id) #1
    elif command == "15a311c3-a872-416e-a2f4-9b8f41712bad":
        proc15a311c3a872416ea2f49b8f41712bad(sender_id, message, data, service_data_bot_need, carousel_id) #2
    elif command == "b63c3343-a6f0-42f9-bd5f-575fdbe43d20":
        procb63c3343a6f042f9bd5f575fdbe43d20(sender_id, message, data, service_data_bot_need, carousel_id) #3
    elif command == "8ce4471c-310e-49c4-bad6-2b82996d23e8":
        proc8ce4471c310e49c4bad62b82996d23e8(sender_id, message, data, service_data_bot_need, carousel_id) #4
    elif command == "ea302a5c-ac3d-477b-8fd2-68a66fb56264":
        procea302a5cac3d477b8fd268a66fb56264(sender_id, message, data, service_data_bot_need, carousel_id) #5
    elif command == "45188a2f-e76f-463d-a930-4c5a53876d70":
        proc45188a2fe76f463da9304c5a53876d70(sender_id, message, data, service_data_bot_need, carousel_id) #Пропустить
    elif command == "c937a519-2897-450e-bc6b-ca9aa2c743e2":
        procc937a5192897450ebc6bca9aa2c743e2(sender_id, message, data, service_data_bot_need, carousel_id) #Отменить
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc8fe801703cea47eb8291e37e9d4751aa(sender_id, message, data, service_data_bot_need, carousel_id):
    #1
    print("stack: proc8fe801703cea47eb8291e37e9d4751aa")
    if GetIdStateForClearData() == "8fe80170-3cea-47eb-8291-e37e9d4751aa":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    procf78d807143864b3f8cd291a0d503f281(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на 1
    return

def proc15a311c3a872416ea2f49b8f41712bad(sender_id, message, data, service_data_bot_need, carousel_id):
    #2
    print("stack: proc15a311c3a872416ea2f49b8f41712bad")
    if GetIdStateForClearData() == "15a311c3-a872-416e-a2f4-9b8f41712bad":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc70a014c3ff72418abb1b94326c535cd6(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на 2
    return

def procb63c3343a6f042f9bd5f575fdbe43d20(sender_id, message, data, service_data_bot_need, carousel_id):
    #3
    print("stack: procb63c3343a6f042f9bd5f575fdbe43d20")
    if GetIdStateForClearData() == "b63c3343-a6f0-42f9-bd5f-575fdbe43d20":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc1c315c3c887a489b95522e1316af7b35(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на 3
    return

def proc8ce4471c310e49c4bad62b82996d23e8(sender_id, message, data, service_data_bot_need, carousel_id):
    #4
    print("stack: proc8ce4471c310e49c4bad62b82996d23e8")
    if GetIdStateForClearData() == "8ce4471c-310e-49c4-bad6-2b82996d23e8":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc12a983c4102340aa85d7d182b9a7e2c5(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на 4
    return

def procea302a5cac3d477b8fd268a66fb56264(sender_id, message, data, service_data_bot_need, carousel_id):
    #5
    print("stack: procea302a5cac3d477b8fd268a66fb56264")
    if GetIdStateForClearData() == "ea302a5c-ac3d-477b-8fd2-68a66fb56264":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc619fd5ff848446fd8f2217bb68bc6a3b(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на 5
    return

def proc45188a2fe76f463da9304c5a53876d70(sender_id, message, data, service_data_bot_need, carousel_id):
    #Пропустить (программный выбор)
    print("stack: proc45188a2fe76f463da9304c5a53876d70")
    if GetIdStateForClearData() == "45188a2f-e76f-463d-a930-4c5a53876d70":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function45188a2fe76f463da9304c5a53876d70(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "save":
        proc01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id) #Подтвердить общая
    return

def proc_function45188a2fe76f463da9304c5a53876d70(sender_id, message, data, service_data_bot_need, carousel_id):
    #Пропустить (функция программного выбора)
    print("stack: proc_function45188a2fe76f463da9304c5a53876d70")
    data.update({"rating":-1})
    data.update({"comment": ""})
    return "save"


def procc937a5192897450ebc6bca9aa2c743e2(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отменить
    print("stack: procc937a5192897450ebc6bca9aa2c743e2")
    if GetIdStateForClearData() == "c937a519-2897-450e-bc6b-ca9aa2c743e2":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Подтверждение не выполнено"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proc01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id):
    #Подтвердить общая (программный выбор)
    print("stack: proc01a9eda608194126be9830251a261e42")
    if GetIdStateForClearData() == "01a9eda6-0819-4126-be98-30251a261e42":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not isinstance(data, dict):
        data = {}
    result_programm_select = proc_function01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id)
    if result_programm_select == "error_in_itilium":
        proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id) #Обращение не подтверждено
    elif result_programm_select == "error_network":
        proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id) #Обращение не подтверждено
    elif result_programm_select == "OK":
        procf5a27e7984da4e5681a8058f67b03c1f(sender_id, message, data, service_data_bot_need, carousel_id) #Обращение подтверждено
    return

def proc_function01a9eda608194126be9830251a261e42(sender_id, message, data, service_data_bot_need, carousel_id):
    #Подтвердить общая (функция программного выбора)
    print("stack: proc_function01a9eda608194126be9830251a261e42")
    rating = data.get('rating')
    comment = data.get('comment')
    is_error, text, state = RequestItilium({"data": {"action": "is_confirm_incident","rating":rating, "comment":comment, "incident":carousel_id,"sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            return "OK" # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proc3ec26f31a5dd4ff7a95fc7c612cf273a(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отклонить (выбор по результатам ввода с клавиатуры)
    print("stack: proc3ec26f31a5dd4ff7a95fc7c612cf273a")
    if GetIdStateForClearData() == "3ec26f31-a5dd-4ff7-a95f-c7c612cf273a":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Введите комментарий"))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "cfbbb503-f7b9-4287-b621-9ec07cbe0afa",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "regular", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "ec26f31-a5dd-4ff7-a95f-c7c612cf273a3", service_data_bot_need, data, carousel_id): #proc_function_expect_user3ec26f31a5dd4ff7a95fc7c612cf273a
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_user3ec26f31a5dd4ff7a95fc7c612cf273a(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_user3ec26f31a5dd4ff7a95fc7c612cf273a")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    if text == "cfbbb503-f7b9-4287-b621-9ec07cbe0afa":
        proccfbbb503f7b94287b6219ec07cbe0afa(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Отмена
        return
    result_programm_select = proc_function3ec26f31a5dd4ff7a95fc7c612cf273a(sender_id, text, data, carousel_id)
    if result_programm_select == "error_network":
        proccfbbb503f7b94287b6219ec07cbe0afa(sender_id, message, data, service_data_bot_need, carousel_id) #Не удалось отклонить
    elif result_programm_select == "error_in_itilium":
        proccfbbb503f7b94287b6219ec07cbe0afa(sender_id, message, data, service_data_bot_need, carousel_id) #Не удалось отклонить
    elif result_programm_select == "OK":
        proc3acf9e3b54a5487191e24a5de6948277(sender_id, message, data, service_data_bot_need, carousel_id) #Отклонено успешно

def proc_function3ec26f31a5dd4ff7a95fc7c612cf273a(sender_id, text, data, carousel_id):
    #Отклонить (функция обработки выбора с клавиатуры)
    print("stack: proc_function3ec26f31a5dd4ff7a95fc7c612cf273a")
    is_error, text, state = RequestItilium({"data": {"action": "is_decline_incident", "incident":carousel_id,"comment":text, "sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            return "OK" # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proc3acf9e3b54a5487191e24a5de6948277(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отклонено успешно
    print("stack: proc3acf9e3b54a5487191e24a5de6948277")
    if GetIdStateForClearData() == "3acf9e3b-54a5-4871-91e2-4a5de6948277":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Обращение оклонено"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proccfbbb503f7b94287b6219ec07cbe0afa(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отмена
    print("stack: proccfbbb503f7b94287b6219ec07cbe0afa")
    if GetIdStateForClearData() == "cfbbb503-f7b9-4287-b621-9ec07cbe0afa":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Не удалось отклонить обращение"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proc42747c5ab75649b0b830bcf82d3dca9c(sender_id, message, data, service_data_bot_need, carousel_id):
    #Назад
    print("stack: proc42747c5ab75649b0b830bcf82d3dca9c")
    if GetIdStateForClearData() == "42747c5a-b756-49b0-b830-bcf82d3dca9c":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Обращение не подтверждено
    return

def procdbb86b04001b4aa587bd0598114130e3(sender_id, message, data, service_data_bot_need, carousel_id):
    #Вывод элемента карусели
    print("stack: procdbb86b04001b4aa587bd0598114130e3")
    if GetIdStateForClearData() == "dbb86b04-001b-4aa5-87bd-0598114130e3":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Выбранное обращение"))

    detail_view = proc_get_user_detail_view_by_iddbb86b04001b4aa587bd0598114130e3(sender_id, carousel_id, data)
    ViberSendMessages(sender_id, TextMessage(text=detail_view))
    return

def proc_get_user_detail_view_by_iddbb86b04001b4aa587bd0598114130e3(sender_id, carousel_id, data):
    #Вывод элемента карусели (функция получения детального представления выбранного элемента карусели)
    print("stack: proc_get_user_detail_view_by_iddbb86b04001b4aa587bd0598114130e3")
    for id, detail_view in data.get('list_open_incidents'):
        if id == carousel_id:
            return detail_view
    return "Не найдено обращение"

def proc7e43a7686c964691abb16ccf4e47e119(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отмена
    print("stack: proc7e43a7686c964691abb16ccf4e47e119")
    if GetIdStateForClearData() == "7e43a768-6c96-4691-abb1-6ccf4e47e119":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Обращение не подтверждено"))
    proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Обращения для подтверждения
    return

def procf5a27e7984da4e5681a8058f67b03c1f(sender_id, message, data, service_data_bot_need, carousel_id):
    #Обращение подтверждено
    print("stack: procf5a27e7984da4e5681a8058f67b03c1f")
    if GetIdStateForClearData() == "f5a27e79-84da-4e56-81a8-058f67b03c1f":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Обращение подтверждено"))
    proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Обращения для подтверждения
    return

def procffaaa8bf92394b6c9ff547b87743d7df(sender_id, message, data, service_data_bot_need, carousel_id):
    #Обращение отклонено
    print("stack: procffaaa8bf92394b6c9ff547b87743d7df")
    if GetIdStateForClearData() == "ffaaa8bf-9239-4b6c-9ff5-47b87743d7df":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Обращение отклонено"))
    proc5160f46d71b8466a8b28db1bf17d5392(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Обращения для подтверждения
    return

def procff766d22eecd4b8a9509ad556751429f(sender_id, message, data, service_data_bot_need, carousel_id):
    #Нет обращений
    print("stack: procff766d22eecd4b8a9509ad556751429f")
    if GetIdStateForClearData() == "ff766d22-eecd-4b8a-9509-ad556751429f":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Нет обращений для подтверждения"))
    proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Выбор действия
    return

def proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id):
    #Последние сообщения (Карусель)
    print("stack: proccdab1713d317452bbbdb8a484d513051")
    if GetIdStateForClearData() == "cdab1713-d317-452b-bbdb-8a484d513051":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "cdab1713-d317-452b-bbdb-8a484d513051", service_data_bot_need, data, carousel_id): #proccdab1713d317452bbbdb8a484d513051
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return

    number_parts = 1;
    temp = service_data_bot_need.get("number_partscdab1713d317452bbbdb8a484d513051")
    if not temp == None:
        number_parts = temp
    result_list = proc_get_list_cortegescdab1713d317452bbbdb8a484d513051(sender_id, data, carousel_id)
    if isinstance(result_list, list):

        ShowCarousel(sender_id, result_list, number_parts)
        service_data_bot_need.update({"number_partscdab1713d317452bbbdb8a484d513051":number_parts})
        if not SaveState(sender_id, "dab1713-d317-452b-bbdb-8a484d513051c", service_data_bot_need, data, carousel_id): #proc_expect_comand_usercdab1713d317452bbbdb8a484d513051
            ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
            GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
            return
    elif result_list == "error_network":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_list == "error_in_itilium":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_list == "OK":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    return

def proc_get_list_cortegescdab1713d317452bbbdb8a484d513051(sender_id, data, carousel_id):
    #Последние сообщения (получение списка кортежей)
    print("stack: proc_get_list_cortegescdab1713d317452bbbdb8a484d513051")
    is_error, text, state = RequestItilium({"data": {"action": "is_get_last_conversations","sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            # data.update({'detail_text':text})
            list = json.loads(text)
            list_ret = []
            list_ret_full = []
            if len(list) == 0:
                ViberSendMessages(sender_id, TextMessage(text="Нет сообщений за последние 5 дней"))
                return "OK"
            for incident in list:
                list_ret.append((incident.get('id'),incident.get('view')))
                list_ret_full.append((incident.get('id'),incident.get('detail_view')))
            data.update({'list_open_incidents_full':list_ret_full,"list_open_incidents": list_ret})
            return list_ret # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние


def proc_expect_comand_usercdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id):
    #Последние сообщения (обработчик выбора пользователя из карусели или команды под ней)
    print("stack: proc_expect_comand_usercdab1713d317452bbbdb8a484d513051")
    id = GetTextCommand(message)
    if id == "cancel":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия(команда "Отменить")
    elif id == "more_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_partscdab1713d317452bbbdb8a484d513051")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_partscdab1713d317452bbbdb8a484d513051": number_parts + 1})
        proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод дополнительных непоместившихся элементов
    elif id == "back_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_partscdab1713d317452bbbdb8a484d513051")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_partscdab1713d317452bbbdb8a484d513051": number_parts - 1})
        proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод предыдущих элементов
    else:
        carousel_id = id
        proc9e625d3af5e246b2b30e56242d8be3e5(sender_id, message, data, service_data_bot_need, carousel_id) #Обработчик вывода (Вывод элемента карусели)
        proc6263c108cd6443a2b3678ab97a445fc7(sender_id, message, data, service_data_bot_need, carousel_id) #Команды элемента (Вывод команд для выбранного элемента карусели)
    return

def proc9e625d3af5e246b2b30e56242d8be3e5(sender_id, message, data, service_data_bot_need, carousel_id):
    #Обработчик вывода
    print("stack: proc9e625d3af5e246b2b30e56242d8be3e5")
    if GetIdStateForClearData() == "9e625d3a-f5e2-46b2-b30e-56242d8be3e5":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}

    detail_view = proc_get_user_detail_view_by_id9e625d3af5e246b2b30e56242d8be3e5(sender_id, carousel_id, data)
    ViberSendMessages(sender_id, TextMessage(text=detail_view))
    return

def proc_get_user_detail_view_by_id9e625d3af5e246b2b30e56242d8be3e5(sender_id, carousel_id, data):
    #Обработчик вывода (функция получения детального представления выбранного элемента карусели)
    print("stack: proc_get_user_detail_view_by_id9e625d3af5e246b2b30e56242d8be3e5")
    for id, detail_view in data.get('list_open_incidents_full'):
        if id == carousel_id:
            return detail_view
    return "Не найден"

def proc6263c108cd6443a2b3678ab97a445fc7(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды элемента (команды элемента карусели)
    print("stack: proc6263c108cd6443a2b3678ab97a445fc7")
    if GetIdStateForClearData() == "6263c108-cd64-43a2-b367-8ab97a445fc7":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "6263c108-cd64-43a2-b367-8ab97a445fc7", service_data_bot_need, data, carousel_id): #proc6263c108cd6443a2b3678ab97a445fc7
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "f7dc6d45-6b09-4b7c-8dff-0942edf2acb5",
        "Text": "Новое сообщение" })
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "11c28422-61c5-4d9f-863b-a2457b97e4ae",
        "Text": "Отмена" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons":buttons}))
    if not SaveState(sender_id, "263c108-cd64-43a2-b367-8ab97a445fc76", service_data_bot_need, data, carousel_id): #proc_expect_user_button_click6263c108cd6443a2b3678ab97a445fc7
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_click6263c108cd6443a2b3678ab97a445fc7(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды элемента (Обработчик выбора из подчиненных команд элемента карусели)
    print("stack: proc_expect_user_button_click6263c108cd6443a2b3678ab97a445fc7")
    command = GetTextCommand(message)
    if command == "f7dc6d45-6b09-4b7c-8dff-0942edf2acb5":
        procf7dc6d456b094b7c8dff0942edf2acb5(sender_id, message, data, service_data_bot_need, carousel_id) #Новое сообщение
    elif command == "11c28422-61c5-4d9f-863b-a2457b97e4ae":
        proc11c2842261c54d9f863ba2457b97e4ae(sender_id, message, data, service_data_bot_need, carousel_id) #Отмена
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def procf7dc6d456b094b7c8dff0942edf2acb5(sender_id, message, data, service_data_bot_need, carousel_id):
    #Новое сообщение (выбор по результатам ввода с клавиатуры)
    print("stack: procf7dc6d456b094b7c8dff0942edf2acb5")
    if GetIdStateForClearData() == "f7dc6d45-6b09-4b7c-8dff-0942edf2acb5":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "44188e7a-8866-457a-8033-cc9e23b1a1ff",
        "Text": "Сообщение не добавлено" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "regular", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "7dc6d45-6b09-4b7c-8dff-0942edf2acb5f", service_data_bot_need, data, carousel_id): #proc_function_expect_userf7dc6d456b094b7c8dff0942edf2acb5
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_function_expect_userf7dc6d456b094b7c8dff0942edf2acb5(sender_id, message, data, service_data_bot_need, carousel_id):
    # Выбор по результатам ввода с клавиатуры. Обработка ввота пользователя
    print("stack: proc_function_expect_userf7dc6d456b094b7c8dff0942edf2acb5")
    if not isinstance(data, dict):
        data = {}
    text = GetTextCommand(message)
    if text == "44188e7a-8866-457a-8033-cc9e23b1a1ff":
        proc44188e7a8866457a8033cc9e23b1a1ff(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Сообщение не добавлено
        return
    result_programm_select = proc_functionf7dc6d456b094b7c8dff0942edf2acb5(sender_id, text, data, carousel_id)
    if result_programm_select == "error_in_itilium":
        proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Последние сообщения
    elif result_programm_select == "error_network":
        proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Последние сообщения
    elif result_programm_select == "OK":
        proc3fb889f893ef403ebaaf6b4e49bb4dd8(sender_id, message, data, service_data_bot_need, carousel_id) #Сообщение добавлено

def proc_functionf7dc6d456b094b7c8dff0942edf2acb5(sender_id, text, data, carousel_id):
    #Новое сообщение (функция обработки выбора с клавиатуры)
    print("stack: proc_functionf7dc6d456b094b7c8dff0942edf2acb5")
    is_error, text, state = RequestItilium({"data": {"action": "is_add_converstaion","incident" : carousel_id,"text":text,"sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            return "OK" # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние

def proc11c2842261c54d9f863ba2457b97e4ae(sender_id, message, data, service_data_bot_need, carousel_id):
    #Отмена
    print("stack: proc11c2842261c54d9f863ba2457b97e4ae")
    if GetIdStateForClearData() == "11c28422-61c5-4d9f-863b-a2457b97e4ae":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Последние сообщения
    return

def proc3fb889f893ef403ebaaf6b4e49bb4dd8(sender_id, message, data, service_data_bot_need, carousel_id):
    #Сообщение добавлено
    print("stack: proc3fb889f893ef403ebaaf6b4e49bb4dd8")
    if GetIdStateForClearData() == "3fb889f8-93ef-403e-baaf-6b4e49bb4dd8":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Сообщение добавлено"))
    proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Последние сообщения
    return

def proc44188e7a8866457a8033cc9e23b1a1ff(sender_id, message, data, service_data_bot_need, carousel_id):
    #Сообщение не добавлено
    print("stack: proc44188e7a8866457a8033cc9e23b1a1ff")
    if GetIdStateForClearData() == "44188e7a-8866-457a-8033-cc9e23b1a1ff":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    ViberSendMessages(sender_id, TextMessage(text="Сообщение не добавлено"))
    proccdab1713d317452bbbdb8a484d513051(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Последние сообщения
    return

def procf6829c8beb464c618ab63bd31f6bc879(sender_id, message, data, service_data_bot_need, carousel_id):
    #Получить статус (Карусель)
    print("stack: procf6829c8beb464c618ab63bd31f6bc879")
    if GetIdStateForClearData() == "f6829c8b-eb46-4c61-8ab6-3bd31f6bc879":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "f6829c8b-eb46-4c61-8ab6-3bd31f6bc879", service_data_bot_need, data, carousel_id): #procf6829c8beb464c618ab63bd31f6bc879
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return

    number_parts = 1;
    temp = service_data_bot_need.get("number_partsf6829c8beb464c618ab63bd31f6bc879")
    if not temp == None:
        number_parts = temp
    result_list = proc_get_list_cortegesf6829c8beb464c618ab63bd31f6bc879(sender_id, data, carousel_id)
    if isinstance(result_list, list):

        ShowCarousel(sender_id, result_list, number_parts)
        service_data_bot_need.update({"number_partsf6829c8beb464c618ab63bd31f6bc879":number_parts})
        if not SaveState(sender_id, "6829c8b-eb46-4c61-8ab6-3bd31f6bc879f", service_data_bot_need, data, carousel_id): #proc_expect_comand_userf6829c8beb464c618ab63bd31f6bc879
            ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
            GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
            return
    elif result_list == "error_network":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    elif result_list == "error_in_itilium":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия
    return

def proc_get_list_cortegesf6829c8beb464c618ab63bd31f6bc879(sender_id, data, carousel_id):
    #Получить статус (получение списка кортежей)
    print("stack: proc_get_list_cortegesf6829c8beb464c618ab63bd31f6bc879")
    is_error, text, state = RequestItilium({"data": {"action": "is_list_open_incidents","sender": sender_id}})
    if is_error:
        text_error = text
        ViberSendMessages(sender_id, TextMessage(text="Ошибка:" + text_error))
        return "error_network" # В процедуре обработке надо направить на нужное состояние
    else:
        if state:
            # data.update({'detail_text':text})
            list = json.loads(text)
            list_ret = []
            list_ret_full = []
            for incident in list:
                list_ret.append((incident.get('id'),incident.get('view')))
                list_ret_full.append((incident.get('id'),incident.get('detail_view')))
            data.update({'list_open_incidents':list_ret_full })
            return list_ret # В процедуре обработке надо направить на нужное состояние, если требуется
        else:
            text_error = text
            ViberSendMessages(sender_id, TextMessage(text=str(text_error)))
            return "error_in_itilium" # В процедуре обработке надо направить на нужное состояние


def proc_expect_comand_userf6829c8beb464c618ab63bd31f6bc879(sender_id, message, data, service_data_bot_need, carousel_id):
    #Получить статус (обработчик выбора пользователя из карусели или команды под ней)
    print("stack: proc_expect_comand_userf6829c8beb464c618ab63bd31f6bc879")
    id = GetTextCommand(message)
    if id == "cancel":
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия(команда "Отменить")
    elif id == "more_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_partsf6829c8beb464c618ab63bd31f6bc879")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_partsf6829c8beb464c618ab63bd31f6bc879": number_parts + 1})
        procf6829c8beb464c618ab63bd31f6bc879(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод дополнительных непоместившихся элементов
    elif id == "back_data":

        number_parts = 1
        temp = service_data_bot_need.get("number_partsf6829c8beb464c618ab63bd31f6bc879")
        if not temp == None:
            number_parts = temp
        service_data_bot_need.update({"number_partsf6829c8beb464c618ab63bd31f6bc879": number_parts - 1})
        procf6829c8beb464c618ab63bd31f6bc879(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на вывод предыдущих элементов
    else:
        carousel_id = id
        procea557c1bbda64ec0a0c7ad3e4f493afc(sender_id, message, data, service_data_bot_need, carousel_id) #Вывод элемента карусели (Вывод элемента карусели)
        proc17c11a9477c8493db93470bdbee77ffc(sender_id, message, data, service_data_bot_need, carousel_id) #Команды карусели (Вывод команд для выбранного элемента карусели)
    return

def procea557c1bbda64ec0a0c7ad3e4f493afc(sender_id, message, data, service_data_bot_need, carousel_id):
    #Вывод элемента карусели
    print("stack: procea557c1bbda64ec0a0c7ad3e4f493afc")
    if GetIdStateForClearData() == "ea557c1b-bda6-4ec0-a0c7-ad3e4f493afc":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}

    detail_view = proc_get_user_detail_view_by_idea557c1bbda64ec0a0c7ad3e4f493afc(sender_id, carousel_id, data)
    ViberSendMessages(sender_id, TextMessage(text=detail_view))
    return

def proc_get_user_detail_view_by_idea557c1bbda64ec0a0c7ad3e4f493afc(sender_id, carousel_id, data):
    #Вывод элемента карусели (функция получения детального представления выбранного элемента карусели)
    print("stack: proc_get_user_detail_view_by_idea557c1bbda64ec0a0c7ad3e4f493afc")
    for id, detail_view in data.get('list_open_incidents'):
        if id == carousel_id:
            return detail_view
    return "Не найден"

def proc17c11a9477c8493db93470bdbee77ffc(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды карусели (команды элемента карусели)
    print("stack: proc17c11a9477c8493db93470bdbee77ffc")
    if GetIdStateForClearData() == "17c11a94-77c8-493d-b934-70bdbee77ffc":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "17c11a94-77c8-493d-b934-70bdbee77ffc", service_data_bot_need, data, carousel_id): #proc17c11a9477c8493db93470bdbee77ffc
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "542a39f9-c585-4d3c-a971-2192a781019f",
        "Text": "Закрыть" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons":buttons}))
    if not SaveState(sender_id, "7c11a94-77c8-493d-b934-70bdbee77ffc1", service_data_bot_need, data, carousel_id): #proc_expect_user_button_click17c11a9477c8493db93470bdbee77ffc
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_click17c11a9477c8493db93470bdbee77ffc(sender_id, message, data, service_data_bot_need, carousel_id):
    #Команды карусели (Обработчик выбора из подчиненных команд элемента карусели)
    print("stack: proc_expect_user_button_click17c11a9477c8493db93470bdbee77ffc")
    command = GetTextCommand(message)
    if command == "542a39f9-c585-4d3c-a971-2192a781019f":
        proc542a39f9c5854d3ca9712192a781019f(sender_id, message, data, service_data_bot_need, carousel_id) #Закрыть
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc542a39f9c5854d3ca9712192a781019f(sender_id, message, data, service_data_bot_need, carousel_id):
    #Закрыть
    print("stack: proc542a39f9c5854d3ca9712192a781019f")
    if GetIdStateForClearData() == "542a39f9-c585-4d3c-a971-2192a781019f":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    procf6829c8beb464c618ab63bd31f6bc879(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Получить статус
    return

def proc6cc30e06b21a4176892b507ee382b3e8(sender_id, message, data, service_data_bot_need, carousel_id):
    #Состояние ошибки при Приветствии (выбор из подчиненных команд)
    print("stack: proc6cc30e06b21a4176892b507ee382b3e8")
    if GetIdStateForClearData() == "6cc30e06-b21a-4176-892b-507ee382b3e8":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    if not SaveState(sender_id, "6cc30e06-b21a-4176-892b-507ee382b3e8", service_data_bot_need, data, carousel_id): #proc6cc30e06b21a4176892b507ee382b3e8
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    ViberSendMessages(sender_id, TextMessage(text="Ошибка сети. Нет доступа к Итилиум. Нажмите \"да\", когда Итилиум будет опубликован."))
    buttons = []
    buttons.append({
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "5c625ad3-ac90-4009-97e7-d2e0b64d18c3",
        "Text": "да" })
    ViberSendMessages(sender_id, KeyboardMessage(min_api_version=4, keyboard={"InputFieldState": "hidden", "Type": "keyboard", "Buttons": buttons}))
    if not SaveState(sender_id, "cc30e06-b21a-4176-892b-507ee382b3e86", service_data_bot_need, data, carousel_id): #proc_expect_user_button_click6cc30e06b21a4176892b507ee382b3e8
        ViberSendMessages(sender_id, TextMessage(text="ERROR SAVE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
        return
    return

def proc_expect_user_button_click6cc30e06b21a4176892b507ee382b3e8(sender_id, message, data, service_data_bot_need, carousel_id):
    #Состояние ошибки при Приветствии (Обработчик выбора из подчиненных команд)
    print("stack: proc_expect_user_button_click6cc30e06b21a4176892b507ee382b3e8")
    command = GetTextCommand(message)
    if command == "5c625ad3-ac90-4009-97e7-d2e0b64d18c3":
        proc5c625ad3ac90400997e7d2e0b64d18c3(sender_id, message, data, service_data_bot_need, carousel_id) #да
    else:
        proc095761bb67d8455bbf094e32d0e8dc4f(sender_id, message, data, service_data_bot_need, carousel_id) #Выбор действия

def proc5c625ad3ac90400997e7d2e0b64d18c3(sender_id, message, data, service_data_bot_need, carousel_id):
    #да
    print("stack: proc5c625ad3ac90400997e7d2e0b64d18c3")
    if GetIdStateForClearData() == "5c625ad3-ac90-4009-97e7-d2e0b64d18c3":
        service_data_bot_need = {}
        carousel_id = ''
        data = {}
    proc02957edd8e984dd4a0aa530f15bba971(sender_id, message, data, service_data_bot_need, carousel_id) #Переход на Приветствие
    return

list_procs = {}
list_procs.update( { '02957edd-8e98-4dd4-a0aa-530f15bba971': proc02957edd8e984dd4a0aa530f15bba971,'02957edd-8e98-4dd4-a0aa-530f15bba971without_registration': True} )
list_procs.update( { '1b68be2d-5a9a-4d06-adb5-9b874e1673ea': proc1b68be2d5a9a4d06adb59b874e1673ea,'1b68be2d-5a9a-4d06-adb5-9b874e1673eawithout_registration': True} )
list_procs.update( { 'b68be2d-5a9a-4d06-adb5-9b874e1673ea1': proc_function_expect_user1b68be2d5a9a4d06adb59b874e1673ea,'b68be2d-5a9a-4d06-adb5-9b874e1673ea1without_registration': True} )
list_procs.update( { '2b3f0bd4-eef0-409c-9ffb-14ffb0d21861': proc2b3f0bd4eef0409c9ffb14ffb0d21861,'2b3f0bd4-eef0-409c-9ffb-14ffb0d21861without_registration': True} )
list_procs.update( { '095761bb-67d8-455b-bf09-4e32d0e8dc4f': proc095761bb67d8455bbf094e32d0e8dc4f,'095761bb-67d8-455b-bf09-4e32d0e8dc4fwithout_registration': False} )
list_procs.update( { '95761bb-67d8-455b-bf09-4e32d0e8dc4f0': proc_expect_user_button_click095761bb67d8455bbf094e32d0e8dc4f,'95761bb-67d8-455b-bf09-4e32d0e8dc4f0without_registration': False} )
list_procs.update( { '76456fc5-a5d3-4b54-81dc-b15c34787790': proc76456fc5a5d34b5481dcb15c34787790,'76456fc5-a5d3-4b54-81dc-b15c34787790without_registration': False} )
list_procs.update( { '6456fc5-a5d3-4b54-81dc-b15c347877907': proc_function_expect_user76456fc5a5d34b5481dcb15c34787790,'6456fc5-a5d3-4b54-81dc-b15c347877907without_registration': False} )
list_procs.update( { '6cc42644-4b07-4aa8-88dc-eecf90f5260a': proc6cc426444b074aa888dceecf90f5260a,'6cc42644-4b07-4aa8-88dc-eecf90f5260awithout_registration': False} )
list_procs.update( { '91d863c1-0ff0-456b-acb0-86818cac8a03': proc91d863c10ff0456bacb086818cac8a03,'91d863c1-0ff0-456b-acb0-86818cac8a03without_registration': False} )
list_procs.update( { '12520952-7570-4b2a-907c-b2e089e0ed77': proc1252095275704b2a907cb2e089e0ed77,'12520952-7570-4b2a-907c-b2e089e0ed77without_registration': False} )
list_procs.update( { '2520952-7570-4b2a-907c-b2e089e0ed771': proc_expect_comand_user1252095275704b2a907cb2e089e0ed77,'2520952-7570-4b2a-907c-b2e089e0ed771without_registration': False} )
list_procs.update( { '84c5c09c-7882-4f2f-819b-d1eef1b3913e': proc84c5c09c78824f2f819bd1eef1b3913e,'84c5c09c-7882-4f2f-819b-d1eef1b3913ewithout_registration': False} )
list_procs.update( { 'ed689fd1-8d59-4246-8b18-92b7a2f97292': proced689fd18d5942468b1892b7a2f97292,'ed689fd1-8d59-4246-8b18-92b7a2f97292without_registration': False} )
list_procs.update( { 'd689fd1-8d59-4246-8b18-92b7a2f97292e': proc_expect_user_button_clicked689fd18d5942468b1892b7a2f97292,'d689fd1-8d59-4246-8b18-92b7a2f97292ewithout_registration': False} )
list_procs.update( { 'bb53668e-eb8e-4153-bdf7-a72781739830': procbb53668eeb8e4153bdf7a72781739830,'bb53668e-eb8e-4153-bdf7-a72781739830without_registration': False} )
list_procs.update( { 'b53668e-eb8e-4153-bdf7-a72781739830b': proc_function_expect_userbb53668eeb8e4153bdf7a72781739830,'b53668e-eb8e-4153-bdf7-a72781739830bwithout_registration': False} )
list_procs.update( { '2ad315bd-42ff-45b8-85ae-cdc9d04c0a9e': proc2ad315bd42ff45b885aecdc9d04c0a9e,'2ad315bd-42ff-45b8-85ae-cdc9d04c0a9ewithout_registration': False} )
list_procs.update( { 'a0981bcc-c8ee-486e-9432-57b9de36f2d1': proca0981bccc8ee486e943257b9de36f2d1,'a0981bcc-c8ee-486e-9432-57b9de36f2d1without_registration': False} )
list_procs.update( { 'e022f99d-4b91-4e8a-8469-546d143ff4e5': proce022f99d4b914e8a8469546d143ff4e5,'e022f99d-4b91-4e8a-8469-546d143ff4e5without_registration': False} )
list_procs.update( { '4cca60de-6e56-43a0-a27b-251f132fafac': proc4cca60de6e5643a0a27b251f132fafac,'4cca60de-6e56-43a0-a27b-251f132fafacwithout_registration': False} )
list_procs.update( { 'cca60de-6e56-43a0-a27b-251f132fafac4': proc_expect_user_button_click4cca60de6e5643a0a27b251f132fafac,'cca60de-6e56-43a0-a27b-251f132fafac4without_registration': False} )
list_procs.update( { '971494b8-473d-4fbe-94c6-86b320392d3a': proc971494b8473d4fbe94c686b320392d3a,'971494b8-473d-4fbe-94c6-86b320392d3awithout_registration': False} )
list_procs.update( { '29615d83-6647-459d-ac36-095a2b7287cc': proc29615d836647459dac36095a2b7287cc,'29615d83-6647-459d-ac36-095a2b7287ccwithout_registration': False} )
list_procs.update( { '5160f46d-71b8-466a-8b28-db1bf17d5392': proc5160f46d71b8466a8b28db1bf17d5392,'5160f46d-71b8-466a-8b28-db1bf17d5392without_registration': False} )
list_procs.update( { '160f46d-71b8-466a-8b28-db1bf17d53925': proc_expect_comand_user5160f46d71b8466a8b28db1bf17d5392,'160f46d-71b8-466a-8b28-db1bf17d53925without_registration': False} )
list_procs.update( { 'dae1f364-0d8a-4eb0-aed3-fc1b63e187aa': procdae1f3640d8a4eb0aed3fc1b63e187aa,'dae1f364-0d8a-4eb0-aed3-fc1b63e187aawithout_registration': False} )
list_procs.update( { 'ae1f364-0d8a-4eb0-aed3-fc1b63e187aad': proc_expect_user_button_clickdae1f3640d8a4eb0aed3fc1b63e187aa,'ae1f364-0d8a-4eb0-aed3-fc1b63e187aadwithout_registration': False} )
list_procs.update( { '5ba6c9fd-cb21-4aa2-972c-4020574f3157': proc5ba6c9fdcb214aa2972c4020574f3157,'5ba6c9fd-cb21-4aa2-972c-4020574f3157without_registration': False} )
list_procs.update( { 'a22a380f-1e10-4600-808c-465bd6ab3777': proca22a380f1e104600808c465bd6ab3777,'a22a380f-1e10-4600-808c-465bd6ab3777without_registration': False} )
list_procs.update( { '22a380f-1e10-4600-808c-465bd6ab3777a': proc_expect_user_button_clicka22a380f1e104600808c465bd6ab3777,'22a380f-1e10-4600-808c-465bd6ab3777awithout_registration': False} )
list_procs.update( { 'f78d8071-4386-4b3f-8cd2-91a0d503f281': procf78d807143864b3f8cd291a0d503f281,'f78d8071-4386-4b3f-8cd2-91a0d503f281without_registration': False} )
list_procs.update( { 'd2aeca92-7521-4a6c-aa98-de3001dd081f': procd2aeca9275214a6caa98de3001dd081f,'d2aeca92-7521-4a6c-aa98-de3001dd081fwithout_registration': False} )
list_procs.update( { '2aeca92-7521-4a6c-aa98-de3001dd081fd': proc_function_expect_userd2aeca9275214a6caa98de3001dd081f,'2aeca92-7521-4a6c-aa98-de3001dd081fdwithout_registration': False} )
list_procs.update( { '4f2c3d62-5e2f-4665-bf75-177d4363273c': proc4f2c3d625e2f4665bf75177d4363273c,'4f2c3d62-5e2f-4665-bf75-177d4363273cwithout_registration': False} )
list_procs.update( { 'f2c3d62-5e2f-4665-bf75-177d4363273c4': proc_function_expect_user4f2c3d625e2f4665bf75177d4363273c,'f2c3d62-5e2f-4665-bf75-177d4363273c4without_registration': False} )
list_procs.update( { 'f8baff8b-ac01-4776-849f-f22db27006da': procf8baff8bac014776849ff22db27006da,'f8baff8b-ac01-4776-849f-f22db27006dawithout_registration': False} )
list_procs.update( { '70a014c3-ff72-418a-bb1b-94326c535cd6': proc70a014c3ff72418abb1b94326c535cd6,'70a014c3-ff72-418a-bb1b-94326c535cd6without_registration': False} )
list_procs.update( { '1c315c3c-887a-489b-9552-2e1316af7b35': proc1c315c3c887a489b95522e1316af7b35,'1c315c3c-887a-489b-9552-2e1316af7b35without_registration': False} )
list_procs.update( { '12a983c4-1023-40aa-85d7-d182b9a7e2c5': proc12a983c4102340aa85d7d182b9a7e2c5,'12a983c4-1023-40aa-85d7-d182b9a7e2c5without_registration': False} )
list_procs.update( { '619fd5ff-8484-46fd-8f22-17bb68bc6a3b': proc619fd5ff848446fd8f2217bb68bc6a3b,'619fd5ff-8484-46fd-8f22-17bb68bc6a3bwithout_registration': False} )
list_procs.update( { 'e6d53aa2-210b-4ed3-8e9f-5e6cea9bc777': proce6d53aa2210b4ed38e9f5e6cea9bc777,'e6d53aa2-210b-4ed3-8e9f-5e6cea9bc777without_registration': False} )
list_procs.update( { 'd4540438-06d1-401f-87b5-ab49f4142f18': procd454043806d1401f87b5ab49f4142f18,'d4540438-06d1-401f-87b5-ab49f4142f18without_registration': False} )
list_procs.update( { '4540438-06d1-401f-87b5-ab49f4142f18d': proc_expect_user_button_clickd454043806d1401f87b5ab49f4142f18,'4540438-06d1-401f-87b5-ab49f4142f18dwithout_registration': False} )
list_procs.update( { '8fe80170-3cea-47eb-8291-e37e9d4751aa': proc8fe801703cea47eb8291e37e9d4751aa,'8fe80170-3cea-47eb-8291-e37e9d4751aawithout_registration': False} )
list_procs.update( { '15a311c3-a872-416e-a2f4-9b8f41712bad': proc15a311c3a872416ea2f49b8f41712bad,'15a311c3-a872-416e-a2f4-9b8f41712badwithout_registration': False} )
list_procs.update( { 'b63c3343-a6f0-42f9-bd5f-575fdbe43d20': procb63c3343a6f042f9bd5f575fdbe43d20,'b63c3343-a6f0-42f9-bd5f-575fdbe43d20without_registration': False} )
list_procs.update( { '8ce4471c-310e-49c4-bad6-2b82996d23e8': proc8ce4471c310e49c4bad62b82996d23e8,'8ce4471c-310e-49c4-bad6-2b82996d23e8without_registration': False} )
list_procs.update( { 'ea302a5c-ac3d-477b-8fd2-68a66fb56264': procea302a5cac3d477b8fd268a66fb56264,'ea302a5c-ac3d-477b-8fd2-68a66fb56264without_registration': False} )
list_procs.update( { '45188a2f-e76f-463d-a930-4c5a53876d70': proc45188a2fe76f463da9304c5a53876d70,'45188a2f-e76f-463d-a930-4c5a53876d70without_registration': False} )
list_procs.update( { 'c937a519-2897-450e-bc6b-ca9aa2c743e2': procc937a5192897450ebc6bca9aa2c743e2,'c937a519-2897-450e-bc6b-ca9aa2c743e2without_registration': False} )
list_procs.update( { '01a9eda6-0819-4126-be98-30251a261e42': proc01a9eda608194126be9830251a261e42,'01a9eda6-0819-4126-be98-30251a261e42without_registration': False} )
list_procs.update( { '3ec26f31-a5dd-4ff7-a95f-c7c612cf273a': proc3ec26f31a5dd4ff7a95fc7c612cf273a,'3ec26f31-a5dd-4ff7-a95f-c7c612cf273awithout_registration': False} )
list_procs.update( { 'ec26f31-a5dd-4ff7-a95f-c7c612cf273a3': proc_function_expect_user3ec26f31a5dd4ff7a95fc7c612cf273a,'ec26f31-a5dd-4ff7-a95f-c7c612cf273a3without_registration': False} )
list_procs.update( { '3acf9e3b-54a5-4871-91e2-4a5de6948277': proc3acf9e3b54a5487191e24a5de6948277,'3acf9e3b-54a5-4871-91e2-4a5de6948277without_registration': False} )
list_procs.update( { 'cfbbb503-f7b9-4287-b621-9ec07cbe0afa': proccfbbb503f7b94287b6219ec07cbe0afa,'cfbbb503-f7b9-4287-b621-9ec07cbe0afawithout_registration': False} )
list_procs.update( { '42747c5a-b756-49b0-b830-bcf82d3dca9c': proc42747c5ab75649b0b830bcf82d3dca9c,'42747c5a-b756-49b0-b830-bcf82d3dca9cwithout_registration': False} )
list_procs.update( { 'dbb86b04-001b-4aa5-87bd-0598114130e3': procdbb86b04001b4aa587bd0598114130e3,'dbb86b04-001b-4aa5-87bd-0598114130e3without_registration': False} )
list_procs.update( { '7e43a768-6c96-4691-abb1-6ccf4e47e119': proc7e43a7686c964691abb16ccf4e47e119,'7e43a768-6c96-4691-abb1-6ccf4e47e119without_registration': False} )
list_procs.update( { 'f5a27e79-84da-4e56-81a8-058f67b03c1f': procf5a27e7984da4e5681a8058f67b03c1f,'f5a27e79-84da-4e56-81a8-058f67b03c1fwithout_registration': False} )
list_procs.update( { 'ffaaa8bf-9239-4b6c-9ff5-47b87743d7df': procffaaa8bf92394b6c9ff547b87743d7df,'ffaaa8bf-9239-4b6c-9ff5-47b87743d7dfwithout_registration': False} )
list_procs.update( { 'ff766d22-eecd-4b8a-9509-ad556751429f': procff766d22eecd4b8a9509ad556751429f,'ff766d22-eecd-4b8a-9509-ad556751429fwithout_registration': False} )
list_procs.update( { 'cdab1713-d317-452b-bbdb-8a484d513051': proccdab1713d317452bbbdb8a484d513051,'cdab1713-d317-452b-bbdb-8a484d513051without_registration': False} )
list_procs.update( { 'dab1713-d317-452b-bbdb-8a484d513051c': proc_expect_comand_usercdab1713d317452bbbdb8a484d513051,'dab1713-d317-452b-bbdb-8a484d513051cwithout_registration': False} )
list_procs.update( { '9e625d3a-f5e2-46b2-b30e-56242d8be3e5': proc9e625d3af5e246b2b30e56242d8be3e5,'9e625d3a-f5e2-46b2-b30e-56242d8be3e5without_registration': False} )
list_procs.update( { '6263c108-cd64-43a2-b367-8ab97a445fc7': proc6263c108cd6443a2b3678ab97a445fc7,'6263c108-cd64-43a2-b367-8ab97a445fc7without_registration': False} )
list_procs.update( { '263c108-cd64-43a2-b367-8ab97a445fc76': proc_expect_user_button_click6263c108cd6443a2b3678ab97a445fc7,'263c108-cd64-43a2-b367-8ab97a445fc76without_registration': False} )
list_procs.update( { 'f7dc6d45-6b09-4b7c-8dff-0942edf2acb5': procf7dc6d456b094b7c8dff0942edf2acb5,'f7dc6d45-6b09-4b7c-8dff-0942edf2acb5without_registration': False} )
list_procs.update( { '7dc6d45-6b09-4b7c-8dff-0942edf2acb5f': proc_function_expect_userf7dc6d456b094b7c8dff0942edf2acb5,'7dc6d45-6b09-4b7c-8dff-0942edf2acb5fwithout_registration': False} )
list_procs.update( { '11c28422-61c5-4d9f-863b-a2457b97e4ae': proc11c2842261c54d9f863ba2457b97e4ae,'11c28422-61c5-4d9f-863b-a2457b97e4aewithout_registration': False} )
list_procs.update( { '3fb889f8-93ef-403e-baaf-6b4e49bb4dd8': proc3fb889f893ef403ebaaf6b4e49bb4dd8,'3fb889f8-93ef-403e-baaf-6b4e49bb4dd8without_registration': False} )
list_procs.update( { '44188e7a-8866-457a-8033-cc9e23b1a1ff': proc44188e7a8866457a8033cc9e23b1a1ff,'44188e7a-8866-457a-8033-cc9e23b1a1ffwithout_registration': False} )
list_procs.update( { 'f6829c8b-eb46-4c61-8ab6-3bd31f6bc879': procf6829c8beb464c618ab63bd31f6bc879,'f6829c8b-eb46-4c61-8ab6-3bd31f6bc879without_registration': False} )
list_procs.update( { '6829c8b-eb46-4c61-8ab6-3bd31f6bc879f': proc_expect_comand_userf6829c8beb464c618ab63bd31f6bc879,'6829c8b-eb46-4c61-8ab6-3bd31f6bc879fwithout_registration': False} )
list_procs.update( { 'ea557c1b-bda6-4ec0-a0c7-ad3e4f493afc': procea557c1bbda64ec0a0c7ad3e4f493afc,'ea557c1b-bda6-4ec0-a0c7-ad3e4f493afcwithout_registration': False} )
list_procs.update( { '17c11a94-77c8-493d-b934-70bdbee77ffc': proc17c11a9477c8493db93470bdbee77ffc,'17c11a94-77c8-493d-b934-70bdbee77ffcwithout_registration': False} )
list_procs.update( { '7c11a94-77c8-493d-b934-70bdbee77ffc1': proc_expect_user_button_click17c11a9477c8493db93470bdbee77ffc,'7c11a94-77c8-493d-b934-70bdbee77ffc1without_registration': False} )
list_procs.update( { '542a39f9-c585-4d3c-a971-2192a781019f': proc542a39f9c5854d3ca9712192a781019f,'542a39f9-c585-4d3c-a971-2192a781019fwithout_registration': False} )
list_procs.update( { '6cc30e06-b21a-4176-892b-507ee382b3e8': proc6cc30e06b21a4176892b507ee382b3e8,'6cc30e06-b21a-4176-892b-507ee382b3e8without_registration': False} )
list_procs.update( { 'cc30e06-b21a-4176-892b-507ee382b3e86': proc_expect_user_button_click6cc30e06b21a4176892b507ee382b3e8,'cc30e06-b21a-4176-892b-507ee382b3e86without_registration': False} )
list_procs.update( { '5c625ad3-ac90-4009-97e7-d2e0b64d18c3': proc5c625ad3ac90400997e7d2e0b64d18c3,'5c625ad3-ac90-4009-97e7-d2e0b64d18c3without_registration': False} )

def GetIdFirstState():
    print("stack: GetIdFirstState")
    return "02957edd-8e98-4dd4-a0aa-530f15bba971"

def SetFlagStopQuery(sender_id):
    print("stack: SetFlagStopQuery")
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_flags_user',))
        need_stop_check = False
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_flags_user (id serial PRIMARY KEY, sender_id varchar(50), flag_id varchar(36) );")
            need_stop_check = True

        if need_stop_check:
            conn.commit()
            return True
        else:
            cur.execute("SELECT sender_id, flag_id FROM data_flags_user WHERE sender_id = %s", (sender_id,))
            if cur.rowcount > 0:
                result_query = cur.fetchone()
                if result_query[1] == "1": #Удалим флаг
                    cur.execute("DELETE FROM data_flags_user WHERE sender_id = %s", (sender_id,));
                    conn.commit()
                    return True
                else:
                    cur.execute("DELETE FROM data_flags_user WHERE sender_id = %s", (sender_id,));
                    conn.commit()
                    return True
            else:
                conn.commit()
                return True

       # Make the changes to the database persistent
        conn.commit()
        return True
        # Close communication with the database
    except Exception as e:
        print("Error on SetFlagStopQuery:" + e.args[0])
        return False
    finally:
        cur.close()
        conn.close()

def SetFlagStartQuery(sender_id):
    print("stack: SetFlagStartQuery")
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_flags_user',))
        need_stop_check = True
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_flags_user (id serial PRIMARY KEY, sender_id varchar(50), flag_id varchar(36) );")
            need_stop_check = False

        need_new_string = False
        if need_stop_check:
            cur.execute("SELECT sender_id, flag_id FROM data_flags_user WHERE sender_id = %s", (sender_id,))
            if cur.rowcount > 0:
                result_query = cur.fetchone()
                if result_query[1] == "1": #Запрос задан - мы просто ждем
                    conn.commit()
                    return False
                else: # удалим строку и вскинем флаг и вернем True
                    cur.execute("DELETE FROM data_flags_user WHERE sender_id = %s", (sender_id,));
                    need_new_string = True
            else: #вскинем флаг и вернем True
                need_new_string = True
        else: #вскинем флаг и вернем True
            need_new_string = True
        if need_new_string == True:
            # Pass data to fill a query placeholders and let Psycopg perform
            # the correct conversion (no more SQL injections!)
            cur.execute("INSERT INTO data_flags_user (sender_id, flag_id) VALUES (%s, %s)",
                (sender_id, "1"))
       # Make the changes to the database persistent
        conn.commit()
        return True
        # Close communication with the database
    except Exception as e:
        print("Error on SetFlagStartQuery:" + e.args[0])
        return True
    finally:
        cur.close()
        conn.close()

def GetFlagStopQuery(sender_id):
    print("stack: GetFlagStopQuery")
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_flags_user',))
        need_stop_check = False
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_flags_user (id serial PRIMARY KEY, sender_id varchar(50), flag_id varchar(36) );")
            need_stop_check = True


        if need_stop_check:
            conn.commit()
            return False
        else:
            cur.execute("SELECT sender_id, flag_id FROM data_flags_user WHERE sender_id = %s", (sender_id,))
            if cur.rowcount > 0:
                result_query = cur.fetchone()
                if result_query[1] == "1": #Запрос задан - мы просто ждем
                    conn.commit()
                    return True
                else:
                    cur.execute("DELETE FROM data_flags_user WHERE sender_id = %s", (sender_id,));
                    conn.commit()
                    return False
            else:
                conn.commit()
                return False

       # Make the changes to the database persistent
        conn.commit()
        return False
        # Close communication with the database
    except Exception as e:
        print("Error on GetFlagStopQuery:" + e.args[0])
        return False
    finally:
        cur.close()
        conn.close()

def RequestItilium(dict_data):
    print("stack: RequestItilium")
    try:
       quote = "\""
       response = requests.post(address_api_itilium, data=json.dumps(dict_data).encode('utf-8'),
                            auth=(login_itilium, password_itilium))
       code = response.status_code
       description = response.text
       print("  code: " + str(code))
       print("  description: " + description)
       if (code == 200):
           return False, description, True
       else:
           return False, str(code) + ' ' + description, False
    except:
       return True, "Ошибка соединения с Итилиум. Обратитесь к администратору.", False

def GetIdStateForClearData():
    print("stack: GetIdStateForClearData")
    return "095761bb-67d8-455b-bf09-4e32d0e8dc4f"

def GoToStateFirst(sender_id, message, state_id, data, data_user, carousel_id):
    print("stack: GoToStateFirst")
    GoToStateByID(sender_id, message, state_id, data, data_user, carousel_id)
    return

def GoToStateError(sender_id, message, state_id, data, data_user, carousel_id):
    print("stack: GoToStateError")
    GoToStateByID(sender_id, message, state_id, data, data_user, carousel_id)
    return

def GoToStateByID(sender_id, message, state_id, service_data_bot_need, data_user, carousel_id):
    print("stack: GoToStateByID")
    procedure = list_procs.get(state_id)
    if not isinstance(service_data_bot_need, dict):
        service_data_bot_need = {}
    if not isinstance(data_user, dict):
        data_user = {}
    procedure(sender_id, message, data_user, service_data_bot_need, carousel_id)

    return

def GoToCurrentState(sender_id, message, is_registered_user):
    print("stack: GoToCurrentState")
    try:
        result_restore, is_error, state_id, data, data_user, carousel_id = RestoreState(sender_id)
        if result_restore:
            if is_registered_user == False:
                if list_procs.get(state_id + 'without_registration') == True:
                    print("stack: before GoToStateByID: " + state_id)
                    GoToStateByID(sender_id, message, state_id, data, data_user, carousel_id)
                else:
                    GoToStateFirst(sender_id, message, GetIdFirstState(), data, data_user, carousel_id)
            else:
                print("stack: before GoToStateByID: " + state_id)
                GoToStateByID(sender_id, message, state_id, data, data_user, carousel_id)
        else:
            if is_error:
                ViberSendMessages(sender_id, TextMessage(text="ERROR RESTORE STATE"))
                GoToStateError(sender_id, message, GetIdErrorState(), data, data_user, carousel_id)
            else:
                GoToStateFirst(sender_id, message, GetIdFirstState(), data, data_user, carousel_id)
    except Exception as e:
        print("Ошибка при GoToCurrentState: " + e.args[0])
        ViberSendMessages(sender_id, TextMessage(text="ERROR RESTORE STATE"))
        GoToStateError(sender_id, message, GetIdErrorState(), {}, {}, "")
    return

def SetHooksIfNeed():
    print("stack: SetHooksIfNeed")
    need_hook = False
    try:
        need_drop = False
        DATABASE_URL = os.environ['DATABASE_URL']
        # Connect to an existing database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Open a cursor to perform database operations
        cur = conn.cursor()
        cur.execute("select * from information_schema.tables where table_name=%s", ('data_hooks',))
        if(cur.rowcount == 0):
            # Execute a command: this creates a new table
            cur.execute("CREATE TABLE data_hooks (id serial PRIMARY KEY, state TEXT );")
            need_hook = True
        else:
            cur.execute("SELECT state FROM data_hooks")
            result_query = cur.fetchone()
            if(result_query == None):
                need_hook = True
            elif not result_query[0] == "1":
                need_hook = True
                need_drop = True
            else: #result_query[0] == "1":
                need_hook = False

        if need_hook:
            if need_drop:
                cur.execute("DELETE FROM data_hooks");
            viber = Api(BotConfiguration(
                name='Itilium-bot',
                avatar='http://site.com/avatar.jpg',
                auth_token=auth_token_out
                ))
            viber.unset_webhook()
            viber.set_webhook(request.url)

            cur.execute("INSERT INTO data_hooks (state) VALUES (%s)",
                  ("1",))
        conn.commit()
    except Exception as e:
        return False, False, e
    finally:
        cur.close()
        conn.close()
    return True, need_hook, ""

app = Flask(__name__)

viber = Api(BotConfiguration(
    name='Itilium-bot',
    avatar='http://site.com/avatar.jpg',
    auth_token=auth_token_out
))

@app.route('/',  methods=['GET'])
def IncomingGet():
    state, need_hook, error = SetHooksIfNeed()
    if state:
        if need_hook:
            return "Регистрация бота прошла успешно"
        else:
            return "Бот был зарегистрирован ранее"
    else:
        return "Ошибка при регистрации бота." + error.args[0] + "\n Попробуйте вручную (см. документацию)"

@app.route('/',  methods=['POST'])
def incoming():
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        sender_id = viber_request.sender.id
        message = viber_request.message
        if ExistNotDeliveredCommands(sender_id):
            print("Есть недоставленные сообщения от бота для пользователя. Не обрабатываем")
            return Response(status=200)
        if GetFlagStopQuery(sender_id) == True:
            print("Повторный запрос")
            return Response(status=200)
        else:
            if SetFlagStartQuery(sender_id) == True:
                try:
                    is_registered_user = GetIsRegisteredUser(sender_id)
                    GoToCurrentState(sender_id, message, is_registered_user)
                except Exception as e:
                    print ("Error:"+ e.args[0])
                finally:
                    SetFlagStopQuery(sender_id)
            else:
                print("Повторный запрос")
                return Response(status=200)

    elif isinstance(viber_request, ViberSubscribedRequest):
        ViberSendMessages(viber_request.sender.id, TextMessage(text="Вы зарегистрированы"))
    elif isinstance(viber_request, ViberFailedRequest):
        onFailedDeliveredMessage(viber_request._message_token, viber_request._user_id)
        print("НЕ Доставлено " + str(viber_request._message_token))
    elif isinstance(viber_request, ViberDeliveredRequest):
        onDeliveredMessage(viber_request._message_token, viber_request._user_id)
        print("Доставлено " + str(viber_request._message_token))
    elif isinstance(viber_request, ViberConversationStartedRequest) :
        ViberSendMessages(viber_request.sender.id, [TextMessage(text="Добрый день. Вы подписались на бота Итилиум")])

    return Response(status=200)
