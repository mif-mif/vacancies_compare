import requests
import dotenv
import os
from terminaltables import AsciiTable


def get_hh_requested_vacancies(requested_vacancy, town_id, days_amount, page_number=1):
    payload = {'text': requested_vacancy,
               'page': page_number,
               'per_page': 100,
               'area': town_id,
               'period': days_amount,
               'only_with_salary': True
               }
    requested_vacancy_url = 'https://api.hh.ru/vacancies'
    response = requests.get(requested_vacancy_url, payload)
    response.raise_for_status()
    server_response = response.json()
    requested_vacancies = server_response.get('items')
    vacancies_amount = server_response.get('found')
    pages_amount = server_response.get('pages')
    return requested_vacancies, vacancies_amount, pages_amount


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
    server_response = response.json()
    requested_vacancies = server_response['objects']
    vacancies_amount = server_response.get('total')
    next_page_flag = server_response.get('more')
    return requested_vacancies, vacancies_amount, next_page_flag


def calculate_salary(payment_from, payment_to):
    salary = 0
    if payment_from and payment_to:
        salary = (payment_from + payment_to) / 2
    elif payment_from:
        salary = payment_from * 1.2
    elif payment_to:
        salary = payment_to * 0.8
    return salary


def predict_hh_rub_salary(requested_vacancies):
    vacancies_processed = 0
    total_salary = 0
    for vacancy in requested_vacancies:
        vacancy_salary = vacancy.get('salary')
        if vacancy_salary.get('currency') != 'RUR':
            continue
        salary = calculate_salary(vacancy['salary']['from'], vacancy['salary']['to'])
        if not salary:
            continue
        vacancies_processed += 1
        total_salary += salary
    average_salary = int(total_salary / vacancies_processed)
    return average_salary, vacancies_processed


def predict_sj_rub_salary(requested_vacancies):
    vacancies_processed = 0
    total_salary = 0
    for vacancy in requested_vacancies:
        salary = calculate_salary(vacancy['payment_from'], vacancy['payment_to'])
        if not salary:
            continue
        vacancies_processed += 1
        total_salary += salary
    average_salary = int(total_salary / vacancies_processed)
    return average_salary, vacancies_processed


def get_hh_developer_vacancies_summary(developer_vacancies, town_id, days_amount):
    hh_developer_vacancies_summary = dict()
    for vacancy in developer_vacancies:
        vacancy_summary = []
        page = 0
        pages_amount = 1
        while page <= pages_amount:
            requested_vacancies, vacancies_amount, pages_amount = get_hh_requested_vacancies(vacancy, town_id, days_amount, page_number=page)
            vacancy_summary.extend(requested_vacancies)
            page += 1
        average_salary, vacancies_processed = predict_hh_rub_salary(vacancy_summary)
        hh_developer_vacancies_summary[vacancy] = {'vacancies_found': vacancies_amount,
                                                   'vacancies_processed': vacancies_processed,
                                                   'average_salary': average_salary}
    return hh_developer_vacancies_summary


def get_sj_developer_vacancies_summary(developer_vacancies, super_job_api_key, catalog_id, town_id):
    sj_developer_vacancies_summary = dict()
    for vacancy in developer_vacancies:
        vacancy_summary = []
        next_page_flag = True
        page = 0
        while next_page_flag:
            requested_vacancies, vacancies_amount, next_page_flag = get_sj_requested_vacancies(vacancy, super_job_api_key, catalog_id, town_id, page_number=page)
            vacancy_summary.extend(requested_vacancies)
            page += 1
        average_salary, vacancies_processed = predict_sj_rub_salary(vacancy_summary)
        sj_developer_vacancies_summary[vacancy] = {'vacancies_found': vacancies_amount,
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
    days_amount = 30
    hh_developer_vacancies_summary = get_hh_developer_vacancies_summary(developer_vacancies, town_id, days_amount)
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
