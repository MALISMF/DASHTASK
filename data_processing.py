"""
Модуль для загрузки и предобработки данных.
Содержит функции для получения данных из внешних источников и заполнения пропущенных значений.
"""
from typing import List, Optional

import pandas as pd


def load_data() -> pd.DataFrame:
    """
    Загружает данные из внешнего CSV источника.
    
    Returns:
        pd.DataFrame: Загруженный датафрейм с данными.
    """
    data_url = "https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv"
    return pd.read_csv(data_url)


def fill_missing_data(
    dataframe: pd.DataFrame, 
    selected_year: int, 
    countries: List[str]
) -> pd.DataFrame:
    """
    Заполняет пропущенные данные для выбранного года данными за ближайший предыдущий год.
    
    Args:
        dataframe: Исходный датафрейм с данными
        selected_year: Целевой год для отображения данных
        countries: Список стран для обработки
        
    Returns:
        pd.DataFrame: Датафрейм с заполненными данными за выбранный год
    """
    result_records = []
    
    for country in countries:
        country_data = dataframe[dataframe['country'] == country]
        year_data = get_country_data_for_year(country_data, selected_year)
        
        if not year_data.empty:
            # Данные за выбранный год есть
            year_data = add_imputation_metadata(year_data, False, selected_year)
            result_records.append(year_data)
        else:
            # Ищем данные за ближайший предыдущий год
            previous_year_data = get_previous_year_data(country_data, selected_year)
            if not previous_year_data.empty:
                result_records.append(previous_year_data)
    
    if result_records:
        return pd.concat(result_records, ignore_index=True)
    
    return pd.DataFrame()


def get_country_data_for_year(
    country_data: pd.DataFrame, 
    target_year: int
) -> pd.DataFrame:
    """
    Извлекает данные для страны за конкретный год.
    
    Args:
        country_data: Датафрейм с данными только для одной страны
        target_year: Год, за который нужны данные
        
    Returns:
        pd.DataFrame: Данные за указанный год или пустой датафрейм
    """
    return country_data[country_data['year'] == target_year].copy()


def get_previous_year_data(
    country_data: pd.DataFrame, 
    selected_year: int
) -> pd.DataFrame:
    """
    Находит и подготавливает данные за ближайший предыдущий год.
    
    Args:
        country_data: Датафрейм с данными только для одной страны
        selected_year: Целевой год
        
    Returns:
        pd.DataFrame: Датафрейм с данными за ближайший предыдущий год
                      или пустой датафрейм, если предыдущих лет нет
    """
    available_years = sorted(country_data['year'].unique())
    previous_years = [year for year in available_years if year < selected_year]
    
    if not previous_years:
        return pd.DataFrame()
    
    latest_available_year = max(previous_years)
    latest_data = country_data[country_data['year'] == latest_available_year].copy()
    
    # Отмечаем, что данные импутированы
    latest_data = add_imputation_metadata(latest_data, True, latest_available_year)
    latest_data['data_source'] = f'Данные за {latest_available_year}'
    
    # Меняем год на выбранный для корректного отображения
    latest_data['year'] = selected_year
    
    return latest_data


def add_imputation_metadata(
    data: pd.DataFrame, 
    is_imputed: bool, 
    original_year: int
) -> pd.DataFrame:
    """
    Добавляет метаданные об импутации в датафрейм.
    
    Args:
        data: Исходный датафрейм
        is_imputed: Флаг импутации данных
        original_year: Исходный год данных
        
    Returns:
        pd.DataFrame: Датафрейм с добавленными метаданными
    """
    data['is_imputed'] = is_imputed
    data['original_year'] = original_year
    return data