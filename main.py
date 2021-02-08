import requests
import dotenv
import os
from terminaltables import AsciiTable


def get_hh_requested_vacancies(requested_vacancy, page_number=1):
    payload = {'text': requested_vacancy,
               'page': page_number,
               'per_page': 100,
               'area': 1,
               'period': 30,
               'only_with_salary': True
               }
    requested_vacancy_url = 'https://api.hh.ru/vacancies'
    response = requests.get(requested_vacancy_url, payload)
    response.raise_for_status()
    requested_vacancies = response.json().get('items')
    number_vacancies = response.json().get('found')
    return requested_vacancies, number_vacancies


def get_sj_requested_vacancies(requested_vacancy, super_job_api_key, page_number=1):
    payload = {'app_key': super_job_api_key,
               'catalogues': 33,
               'keyword': requested_vacancy,
               'town': 4,
               'page': page_number,
               'count': 100}
    vacancy_url = 'https://api.superjob.ru/2.0/vacancies'
    response = requests.get(vacancy_url, payload)
    response.raise_for_status()
    requested_vacancies = response.json()['objects']
    number_vacancies = response.json().get('total')
    return requested_vacancies, number_vacancies


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
        if not vacancy.get('payment_from') and not vacancy.get('payment_to'):
            continue
        else:
            vacancies_processed, total_salary = calculate_salary(vacancy, vacancies_processed, total_salary, 'payment_from', 'payment_to')
    average_salary = total_salary / vacancies_processed
    return int(average_salary), vacancies_processed


def get_hh_developer_vacancies_summary(developer_vacancies):
    hh_developer_vacancies_summary = dict()
    for vacancy in developer_vacancies:
        vacancy_summary = []
        number_vacancies = get_hh_requested_vacancies(vacancy)[1]
        pages_amount = int(number_vacancies / 100) + 1
        for page in range(pages_amount):
            requested_vacancies = get_hh_requested_vacancies(vacancy, page_number=page)[0]
            for job in requested_vacancies:
                vacancy_summary.append(job)
        average_salary, vacancies_processed = predict_hh_rub_salary(vacancy_summary)
        hh_developer_vacancies_summary[vacancy] = {'vacancies_found': number_vacancies,
                                                   'vacancies_processed': vacancies_processed,
                                                   'average_salary': average_salary}
    return hh_developer_vacancies_summary


def get_sj_developer_vacancies_summary(developer_vacancies, super_job_api_key):
    sj_developer_vacancies_summary = dict()
    for vacancy in developer_vacancies:
        vacancy_summary = []
        number_vacancies = get_sj_requested_vacancies(vacancy, super_job_api_key)[1]
        pages_amount = int(number_vacancies / 100) + 1
        for page in range(pages_amount):
            requested_vacancies = get_sj_requested_vacancies(vacancy, super_job_api_key, page_number=page)[0]
            for job in requested_vacancies:
                vacancy_summary.append(job)
        average_salary, vacancies_processed = predict_sj_rub_salary(vacancy_summary)
        sj_developer_vacancies_summary[vacancy] = {'vacancies_found': number_vacancies,
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
    hh_developer_vacancies_summary = get_hh_developer_vacancies_summary(developer_vacancies)
    hh_vacancies_table = get_vacancies_table(hh_developer_vacancies_summary, hh_title)
    print(hh_vacancies_table)

    sj_title = 'SuperJob Moscow'
    sj_developer_vacancies_summary = get_sj_developer_vacancies_summary(developer_vacancies, super_job_api_key)
    sj_vacancies_table = get_vacancies_table(sj_developer_vacancies_summary, sj_title)
    print(sj_vacancies_table)


if __name__ == '__main__':
    main()
