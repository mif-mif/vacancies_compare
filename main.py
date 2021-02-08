import requests
import dotenv
import os
from terminaltables import AsciiTable


def get_hh_requested_vacancies(requested_vacancy, town_id, days, page_number=1):
    payload = {'text': requested_vacancy,
               'page': page_number,
               'per_page': 100,
               'area': town_id,
               'period': days,
               'only_with_salary': True
               }
    requested_vacancy_url = 'https://api.hh.ru/vacancies'
    response = requests.get(requested_vacancy_url, payload)
    response.raise_for_status()
    requested_vacancies = response.json().get('items')
    vacancy_numbers = response.json().get('found')
    pages = response.json().get('pages')
    return requested_vacancies, vacancy_numbers, pages


def get_sj_requested_vacancies(requested_vacancy, super_job_api_key, catalog_id, town_id, page_number=1):
    payload = {'app_key': super_job_api_key,
               'catalogues': catalog_id,
               'keyword': requested_vacancy,
               'town': town_id,
               'page': page_number,
               'count': 100}
    vacancy_url = 'https://api.superjob.ru/2.0/vacancies'
    response = requests.get(vacancy_url, payload)
    response.raise_for_status()
    requested_vacancies = response.json()['objects']
    vacancy_numbers = response.json().get('total')
    next_page_flag = response.json().get('more')
    return requested_vacancies, vacancy_numbers, next_page_flag


def calculate_salary(vacancy_salary, vacancies_processed, total_salary, payment_from, payment_to):
    if vacancy_salary.get(payment_from) and vacancy_salary.get(payment_to):
        vacancies_processed += 1
        total_salary += (vacancy_salary.get(payment_from) + vacancy_salary.get(payment_to)) / 2
    elif vacancy_salary.get(payment_from):
        vacancies_processed += 1
        total_salary += vacancy_salary.get(payment_from) * 1.2
    elif vacancy_salary.get(payment_to):
        vacancies_processed += 1
        total_salary += vacancy_salary.get(payment_to) * 0.8
    return vacancies_processed, total_salary


def predict_hh_rub_salary(requested_vacancies):
    vacancies_processed = 0
    total_salary = 0
    for vacancy in requested_vacancies:
        vacancy_salary = vacancy.get('salary')
        if vacancy_salary.get('currency') == 'RUR':
            vacancies_processed, total_salary = calculate_salary(vacancy_salary, vacancies_processed, total_salary, 'from', 'to')
    average_salary = total_salary / vacancies_processed
    return int(average_salary), vacancies_processed


def predict_sj_rub_salary(requested_vacancies):
    vacancies_processed = 0
    total_salary = 0
    for vacancy in requested_vacancies:
        vacancies_processed, total_salary = calculate_salary(vacancy, vacancies_processed, total_salary, 'payment_from', 'payment_to')
    average_salary = total_salary / vacancies_processed
    return int(average_salary), vacancies_processed


def get_hh_developer_vacancies_summary(developer_vacancies, town_id, days):
    hh_developer_vacancies_summary = dict()
    for vacancy in developer_vacancies:
        vacancy_summary = []
        vacancy_numbers, pages = get_hh_requested_vacancies(vacancy, town_id, days)[1:]
        page = 0
        while page <= pages:
            requested_vacancies = get_hh_requested_vacancies(vacancy, town_id, days, page_number=page)[0]
            vacancy_summary.extend(requested_vacancies)
            page += 1
        average_salary, vacancies_processed = predict_hh_rub_salary(vacancy_summary)
        hh_developer_vacancies_summary[vacancy] = {'vacancies_found': vacancy_numbers,
                                                   'vacancies_processed': vacancies_processed,
                                                   'average_salary': average_salary}
    return hh_developer_vacancies_summary


def get_sj_developer_vacancies_summary(developer_vacancies, super_job_api_key, catalog_id, town_id):
    sj_developer_vacancies_summary = dict()
    for vacancy in developer_vacancies:
        vacancy_summary = []
        vacancy_numbers = get_sj_requested_vacancies(vacancy, super_job_api_key, catalog_id, town_id)[1]
        next_page_flag = True
        page = 0
        while next_page_flag:
            requested_vacancies, next_page_flag = get_sj_requested_vacancies(vacancy, super_job_api_key, catalog_id, town_id, page_number=page)[0::2]
            vacancy_summary.extend(requested_vacancies)
            page += 1
        average_salary, vacancies_processed = predict_sj_rub_salary(vacancy_summary)
        sj_developer_vacancies_summary[vacancy] = {'vacancies_found': vacancy_numbers,
                                                   'vacancies_processed': vacancies_processed,
                                                   'average_salary': average_salary}
    return sj_developer_vacancies_summary


def get_vacancies_table(developer_vacancies_summary, title):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for languages, attributes in developer_vacancies_summary.items():
        table_data.append(
            [languages, attributes['vacancies_found'], attributes['vacancies_processed'], attributes['average_salary']])
    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[4] = 'right'
    return table_instance.table


def main():
    dotenv.load_dotenv()
    super_job_api_key = os.getenv('SUPER_JOB_API_KEY')
    developer_vacancies = ['Python',
                           'Java',
                           'JavaScript',
                           'C#',
                           'PHP',
                           'C++',
                           'Swift',
                           'TypeScript',
                           'Kotlin',
                           'Go',
                           'Ruby'
                           ]

    hh_title = 'HeadHunter Moscow'
    town_id = 1
    days = 30
    hh_developer_vacancies_summary = get_hh_developer_vacancies_summary(developer_vacancies, town_id, days)
    hh_vacancies_table = get_vacancies_table(hh_developer_vacancies_summary, hh_title)
    print(hh_vacancies_table)

    sj_title = 'SuperJob Moscow'
    catalog_id = 33
    town_id = 4
    sj_developer_vacancies_summary = get_sj_developer_vacancies_summary(developer_vacancies, super_job_api_key, catalog_id, town_id)
    sj_vacancies_table = get_vacancies_table(sj_developer_vacancies_summary, sj_title)
    print(sj_vacancies_table)


if __name__ == '__main__':
    main()
