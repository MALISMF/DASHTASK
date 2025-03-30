import pandas as pd

def load_data():
    return pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

def fill_missing_data(dataframe, selected_year, countries):
    """
    Для каждой страны из списка проверяет наличие данных за выбранный год.
    Если данных нет, берет данные за ближайший предыдущий год.
    """
    result_df = pd.DataFrame()
    
    for country in countries:
        # Фильтруем данные только для текущей страны
        country_data = dataframe[dataframe['country'] == country]
        
        # Проверяем, есть ли данные за выбранный год
        year_data = country_data[country_data['year'] == selected_year]
        
        if len(year_data) > 0:
            # Данные за выбранный год есть, используем их
            # Добавим колонку is_imputed со значением False, чтобы обозначить оригинальные данные
            year_data = year_data.copy()
            year_data['is_imputed'] = False
            year_data['original_year'] = selected_year
            result_df = pd.concat([result_df, year_data])
        else:
            # Данных за выбранный год нет, ищем ближайший предыдущий год
            available_years = sorted(country_data['year'].unique())
            previous_years = [year for year in available_years if year < selected_year]
            
            if previous_years:  # Если есть предыдущие годы
                latest_available_year = max(previous_years)
                latest_data = country_data[country_data['year'] == latest_available_year].copy()
                
                # Отмечаем, что данные восстановлены и содержат источник данных
                latest_data['is_imputed'] = True
                latest_data['original_year'] = latest_available_year
                latest_data['data_source'] = f'Данные за {latest_available_year}'
                
                # Меняем год на выбранный, чтобы он отображался корректно
                latest_data['year'] = selected_year
                
                result_df = pd.concat([result_df, latest_data])
    
    return result_df
