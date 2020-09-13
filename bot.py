from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Location
import states
import config
import os
import ast

TOKEN = config.TOKEN


def start(update, context):
    load_data(update, context)
    context.user_data['state'] = states.STARTED
    text = """Hello, {0}! This bot will help you to remember location of your cars!\n\nYou can store up to 5 cars\n\nTo start use "park" command"""
    update.message.reply_text(text.format(update.message.chat.first_name))
    context.user_data['current_car'] = ''
    context.user_data['actions'] = {'Edit location': edit_location,
                                    'Delete car': delete_car,
                                    'Show location': show_location}
    print('Bot started')
    get_info(update, context)


def load_data(update, context):
    save_data_directory = 'savedata.txt'
    if os.path.exists(save_data_directory):
        save_file = open(save_data_directory, 'r')
        save_data = save_file.readlines()
        if len(save_data) > 0:
            context.user_data['cars'] = ast.literal_eval(save_data[0])
        else:
            context.user_data['cars'] = {}
        print(save_data)
        save_file.close()
    else:
        print('save file created')
        save_file = open(save_data_directory, 'w')
        save_file.close()


def save_data(update, context):
    save_data_directory = 'savedata.txt'
    save_file = open(save_data_directory, 'w')
    save_file.write(str(context.user_data['cars']))
    save_file.close()


def request_car_name(update, context):
    print('request car name')
    print(context.user_data['state'])

    context.user_data['state'] = states.CAR_NAME_REQUESTED
    update.message.reply_text(text='First enter your car name')
    get_info(update, context)


def handle_text_requests(update, context):
    print(context.user_data['state'])
    state = context.user_data['state']
    if state == states.CAR_NAME_REQUESTED:
        context.user_data['cars'][update.message.text] = {}
        context.user_data['current_car'] = update.message.text
        context.user_data['state'] = states.CAR_NAME_ENTERED
        get_location(update, context)
        get_info(update, context)
    elif state == states.CARS_REQUESTED:
        choose_car(update, context)
    elif state == states.CAR_ACTION_REQUESTED:
        choose_action(update, context)


def get_location(update, context):
    print('get location')
    print(context.user_data['state'])

    if context.user_data['state'] == states.CAR_NAME_ENTERED:
        keyboard = ReplyKeyboardMarkup([[KeyboardButton(text='Share my location', request_location=True)]],
                                   resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(text='Now send us your car location', reply_markup=keyboard)
        context.user_data['state'] = states.LOCATION_REQUESTED
    get_info(update, context)


def handle_location(update, context):
    print('handle location')
    print(context.user_data['state'])

    if context.user_data['state'] == states.LOCATION_REQUESTED:
        remove_keyboard = ReplyKeyboardRemove()
        update.message.reply_text(text='Thanks!', reply_markup=remove_keyboard)
        current_car = context.user_data['current_car']
        if len(context.user_data['cars']) < 5:
            context.user_data['cars'][current_car]['location'] = (update.message.location.longitude,
                                                              update.message.location.latitude)
        else:
            key_to_remove = context.user_data['cars'].keys()[-1]
            context.user_data['cars'].pop(key_to_remove)
        on_success_message = 'Parking location of {0} successfully saved!'
        update.message.reply_text(text=on_success_message.format(context.user_data['current_car']))
        context.user_data['current_car'] = ''  # why
        save_data(update, context)
        context.user_data['state'] = states.LOCATION_SHARED
    get_info(update, context)


def choose_car(update, context):
    print('choose car')
    print(context.user_data['state'])

    if context.user_data['state'] == states.CARS_REQUESTED:
        menu = [[KeyboardButton(action_name)] for action_name in context.user_data['actions'].keys()]
        keyboard = ReplyKeyboardMarkup(menu, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(text='Choose action', reply_markup=keyboard)
        context.user_data['current_car'] = update.message.text
        context.user_data['state'] = states.CAR_ACTION_REQUESTED
    get_info(update, context)


def choose_action(update, context):
    print('choose_action')
    print(context.user_data['state'])
    if context.user_data['state'] == states.CAR_ACTION_REQUESTED:
        context.user_data['state'] = states.CAR_ACTION_CHOSEN
        context.user_data['actions'][update.message.text](update, context)
        get_info(update, context)


def edit_location(update, context):
    if context.user_data['state'] == states.CAR_ACTION_CHOSEN:
        context.user_data['state'] = states.CAR_NAME_ENTERED
        get_location(update, context)
        save_data(update, context)


def delete_car(update, context):
    if context.user_data['state'] == states.CAR_ACTION_CHOSEN:
        will_be_removed = context.user_data['current_car']
        context.user_data['cars'].pop(will_be_removed)
        update.message.reply_text(text=context.user_data['current_car']+' was successfully removed')
        context.user_data['current_car'] = ''
        context.user_data['state'] = states.STARTED
        save_data(update, context)


def show_location(update, context):
    print('show loc')
    print(context.user_data['state'])

    if context.user_data['state'] == states.CAR_ACTION_CHOSEN:
        print('ok')
        current_car = context.user_data['current_car']
        location_data = context.user_data['cars'][current_car]['location']
        location = Location(longitude=location_data[0], latitude=location_data[1])
        update.message.reply_location(location=location)
        context.user_data['state'] = states.STARTED


def show_cars(update, context):
    print('show cars')
    print(context.user_data['state'])

    context.user_data['state'] = states.CARS_REQUESTED
    menu = [[KeyboardButton(car_name)] for car_name in context.user_data['cars']]
    keyboard = ReplyKeyboardMarkup(menu, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(text='You have ' + str(len(menu)) + ' car(s)')
    if len(menu) > 0:
        update.message.reply_text(text='Choose car:  ', reply_markup=keyboard)
    get_info(update, context)


def get_info(update, context):
    print(update)
    print(context.user_data)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("park", request_car_name))
    dp.add_handler(CommandHandler("cars", show_cars))

    text_handler = MessageHandler(Filters.text, handle_text_requests)
    location_handler = MessageHandler(Filters.location, handle_location)

    dp.add_handler(text_handler)
    dp.add_handler(location_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
