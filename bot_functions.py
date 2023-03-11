import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from random import randrange
from config import *
import datetime
from database import *


class VKBot:

    def __init__(self):
        self.vk_group = vk_api.VkApi(token=group_token)
        self.vk_user = vk_api.VkApi(token=user_token)
        self.longpoll = VkLongPoll(self.vk_group)

    def write_msg(self, user_id, message):
        self.vk_group.method("messages.send", {'user_id': user_id,
                                               'message': message,
                                               'random_id': randrange(10 ** 7)})

    def name(self, user_id):
        """определение имени пользователя"""
        params = {'access_token': user_token,
                  'user_ids': user_id,
                  'v': '5.131'}
        result_data = self.vk_group.method("users.get", params)
        try:
            for i in result_data:
                for key, value in i.items():
                    first_name = i.get('first_name')
                    return first_name
        except KeyError:
            self.write_msg(user_id, 'Ошибка получения токена, введите токен в переменную - user_token')

    def get_sex(self, user_id):
        """find opposite sex"""
        params = {'access_token': group_token,
                  'v': '5.131',
                  'user_ids': user_id,
                  'fields': 'sex'}
        result_data = self.vk_group.method("users.get", params)
        try:
            for i in result_data:
                if i.get('sex') == 2:
                    opposite_sex = 1
                    return opposite_sex
                elif i.get('sex') == 1:
                    opposite_sex = 2
                    return opposite_sex
        except KeyError:
            self.vk_group.method(user_id, 'Ошибка получения токена, введите токен в переменную - user_token')

    def find_city(self, user_id):
        """find user city id"""
        params = {'access_token': group_token,
                  'v': '5.131',
                  'user_ids': user_id,
                  'fields': 'city'}
        response = self.vk_group.method("users.get", params)
        try:
            for town in response:
                if 'city' in town:
                    city = town.get('city')
                    id = str(city.get('id'))
                    return id
                elif 'city' not in town:
                    self.write_msg(user_id, 'Введите название вашего города: ')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            city_name = event.text
                            id_city = self.find_city_id_by_name(user_id, city_name)
                            if id_city != '' or id_city is not None:
                                return str(id_city)
                            else:
                                break
        except KeyError:
            self.write_msg(user_id, 'Ошибка получения токена')
        return city

    def find_city_id_by_name(self, user_id, city_name):
        """find city id if not in users data"""
        params = {'access_token': user_token,
                  'country_id': 1,
                  'q': f'{city_name}',
                  'need_all': 0,
                  'count': 1000,
                  'v': '5.131'}
        repl = self.vk_group.method('database.getCities', params)
        try:
            information_list = repl['response']
            list_cities = information_list['items']
            for i in list_cities:
                found_city_name = i.get('title')
                if found_city_name == city_name:
                    found_city_id = i.get('id')
                    return int(found_city_id)
        except KeyError:
            self.write_msg(user_id, 'Ошибка получения токена')

    def check_age(self, user_id):
        """user age check"""
        params = {'access_token': user_token,
                  'user_ids': user_id,
                  'fields': 'bdate',
                  'v': '5.131'}
        req = self.vk_group.method("users.get", params)
        try:
            for i in req:
                date = i.get('bdate')
                date_list = date.split('.')
                if len(date_list) == 3:
                    year = int(date_list[2])
                    year_now = int(datetime.date.today().year)
                    age = year_now - year
                    return age
                elif len(date_list) == 2 or date not in req:
                    self.write_msg(user_id, 'Введите ваш возраста (16+): ')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            age = event.text
                            if int(age) < 16:
                                self.write_msg(user_id, 'Минимальный возраст - 16+')
                                self.write_msg(user_id, 'Возвращаюсь в начало')
                                break
                            return age
        except KeyError:
            self.write_msg(user_id, 'Ошибка получения токена')

    def minimum_age(self, user_id):
        """Set minimum age for search"""
        self.write_msg(user_id, 'Укажите минимальный возраст для поиска(Минимальный возраст 16+)')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                search_min_age = event.text
                if int(search_min_age) < 16:
                    self.write_msg(user_id, 'Указанный возраст меньше необходимого')
                    break
                return search_min_age

    def maximum_age(self, user_id):
        """Set maximum age for search"""
        self.write_msg(user_id, 'Укажите максимальный возраст для поиска(Максимальный возраст 90)')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                search_max_age = event.text
                if int(search_max_age) > 90:
                    self.write_msg(user_id, 'Указанный возраст превышает максимальный')
                    return
                return search_max_age

    def collect_users_to_db(self, user_id):
        """find users info and add to database"""
        params = {'access_token': user_token,
                  'v': '5.131',
                  'sex': self.get_sex(user_id),
                  'age_from': self.minimum_age(user_id),
                  'age_to': self.maximum_age(user_id),
                  'city': self.find_city(user_id),
                  'fields': 'is_closed, id, first_name, last_name',
                  'status': '1' or '6',
                  'count': 50}
        req = self.vk_user.method("users.search", params)
        try:
            list_1 = req['items']
            for person_dict in list_1:
                if not person_dict.get('is_closed'):
                    first_name = person_dict.get('first_name')
                    last_name = person_dict.get('last_name')
                    vk_id = str(person_dict.get('id'))
                    vk_link = 'vk.com/id' + str(person_dict.get('id'))
                    add_user_info(first_name, last_name, vk_id, vk_link)
                else:
                    continue
        except KeyError:
            self.write_msg(user_id, 'Ошибка получения токена')

    def select_and_send_top_photo(self, user_id):
        """send top 3 photo"""
        id_nums = {}
        fetch_id = get_user_id()
        for i in range(len(fetch_id)):
            id_nums[i] = fetch_id[randrange(1, len(fetch_id))][0]
            params = {'access_token': user_token,
                      'v': '5.131',
                      'owner_id': id_nums.get(i),
                      'album_id': 'profile',
                      'extended': 1
                      }
            response = self.vk_user.method('photos.get', params)
            photo_info = {}
            for x in range(len(response['items'])):
                photo_info[response['items'][x]['likes']['count']] = {'owner_id': response['items'][x]['owner_id'],
                                                                      'photo_id': response['items'][x]['id'],
                                                                      'likes': response['items'][x]['likes']['count'],
                                                                      'url': response['items'][x]['sizes'][-1]['url']}
            top_three_photo = list(sorted(photo_info.items(), reverse=True)[:3:])
        self.write_msg(user_id, f"vk.com/id{top_three_photo[0][1]['owner_id']}")
        for i in range(len(top_three_photo)):
            self.vk_group.method("messages.send", {'user_id': user_id,
                                                   'random_id': randrange(10 ** 7),
                                                   'attachment': f"photo{top_three_photo[i][1]['owner_id']}_"
                                                                 f"{top_three_photo[i][1]['photo_id']}"
                                                   })
        return f"Отправка фото завершена"

    # def send_photo(self, user_id):
    #     """send photo"""
    #     photo_data = self.select_photo()
    #     for i in range(len(photo_data)):
    #         photo_id = photo_data
    #         self.write_msg(user_id, f"vk.com/id{photo_data[i][1]['owner_id']}")
    #         self.vk_group.method("messages.send", {'user_id': user_id,
    #                                                'random_id': randrange(10 ** 7),
    #                                                'attachment': f"photo{photo_data[i][1]['owner_id']}_"
    #                                                              f"{photo_id[i][1]['photo_id']}"
    #                                                })