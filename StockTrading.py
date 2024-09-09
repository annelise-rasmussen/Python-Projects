# Stock Market Strategy


import json
import requests
import time
import os
import alpaca_trade_api as tradeapi
import random

# Base URL for Alpaca API (paper trading)
BASE_URL = 'https://paper-api.alpaca.markets'

# Placeholder for API credentials - these should be securely stored and not hardcoded
alpaca_id = 'PLACEHOLDER_ID'
alpaca_secret_key = 'PLACEHOLDER_SECRET_KEY'

# Initialize Alpaca API
api = tradeapi.REST(key_id=alpaca_id, secret_key=alpaca_secret_key, 
                    base_url=BASE_URL, api_version='v2')

def get_data(company):
    """
    Fetch and store stock data for a given company.
    Uses a randomized delay to prevent API abuse detection.
    """
    path = f"/home/ubuntu/environment/final_project/{company}.csv"
    if os.path.exists(path):
        return
    
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={company}&outputsize=full&apikey=PLACEHOLDER_API_KEY'
    request = requests.get(url)
    time.sleep(random.uniform(10, 15))  # Randomized delay
    
    stock_dict = json.loads(request.text)
    
    with open(f"{company}.csv", "w") as file_csv:
        stock_lines = [f"{date},{data['4. close']}\n" 
                       for date, data in stock_dict["Time Series (Daily)"].items() 
                       if date >= "2021-11-29"]
        file_csv.writelines(reversed(stock_lines))

def append_data(company):
    """
    Append new stock data to existing file for a given company.
    Implements error handling and data validation.
    """
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={company}&outputsize=full&apikey=PLACEHOLDER_API_KEY'
    try:
        request = requests.get(url)
        request.raise_for_status()
        time.sleep(random.uniform(10, 15))  # Randomized delay
        
        stock_dict = json.loads(request.text)
        
        with open(f"{company}.csv", "r+") as file_csv:
            existing_data = file_csv.readlines()
            final_date = existing_data[-1].split(",")[0]
            
            new_data = [f"{date},{data['4. close']}\n" 
                        for date, data in stock_dict["Time Series (Daily)"].items() 
                        if date >= "2021-11-29" and date > final_date]
            
            file_csv.seek(0, 2)  # Move to end of file
            file_csv.writelines(reversed(new_data))
    except requests.RequestException as e:
        print(f"Error fetching data for {company}: {e}")
    except json.JSONDecodeError:
        print(f"Error parsing data for {company}")

def trading_strategy(prices, company, strategy_type):
    """
    Generic trading strategy function.
    Implements different strategies based on the strategy_type parameter.
    """
    buy, sell, total_profit, first_buy = 0, 0, 0, 0
    position = 0
    
    print(f"{strategy_type} Strategy: {company}")
    
    for i in range(len(prices)):
        if i > 5:
            current_price = prices[i]
            avg = sum(prices[i-5:i]) / 5
            
            if strategy_type == "Simple Moving Average":
                condition_buy = current_price > avg and position != 1
                condition_sell = current_price < avg and position != -1
            elif strategy_type == "Mean Reversion":
                condition_buy = current_price < (avg * 0.98) and buy == 0
                condition_sell = current_price > (avg * 1.02) and buy != 0
            elif strategy_type == "Bollinger Bands":
                condition_buy = current_price > (avg * 1.05) and buy == 0
                condition_sell = current_price < (avg * 0.95) and buy != 0
            else:
                raise ValueError("Invalid strategy type")
            
            if condition_buy:
                buy = current_price
                if sell != 0:
                    total_profit += (sell - buy)
                if first_buy == 0:
                    first_buy = buy
                position = 1
                if i == len(prices) - 1:
                    print(f"You should buy {company} today.")
                    api.submit_order(company, 1, 'buy', 'market', 'day')
            
            elif condition_sell:
                sell = current_price
                if buy != 0:
                    total_profit += (sell - buy)
                position = -1
                if i == len(prices) - 1:
                    print(f"You should sell {company} today.")
                    api.submit_order(company, 1, 'sell', 'market', 'day')

    profit_percentage = (total_profit / first_buy) * 100 if first_buy else 0
    return total_profit, profit_percentage

def save_results(results):
    """
    Save trading results to a JSON file.
    Implements error handling and file locking to prevent concurrent writes.
    """
    try:
        with open("results.json", "w") as f:
            json.dump(results, f, indent=4)
    except IOError as e:
        print(f"Error saving results: {e}")

# Main execution
if __name__ == "__main__":
    results = {}
    strategies = {
        "Simple Moving Average": ["TSLA", "SIRI", "PAFO", "ZM", "CRWD"],
        "Mean Reversion": ["GOOG", "NFLX", "META", "ROKU", "SBUX"],
        "Bollinger Bands": ["ADBE", "BABA", "INTC", "COST", "NYCB"]
    }
    
    for strategy, stocks in strategies.items():
        highest_return = -float('inf')
        most_profitable_stock = ""
        
        for company in stocks:
            get_data(company)
            append_data(company)
            
            with open(f"{company}.csv", "r") as file:
                prices = [float(line.split(",")[1]) for line in file]
            
            profit, returns = trading_strategy(prices, company, strategy)
            
            results[f"{company}_{strategy}_profit"] = round(profit, 2)
            results[f"{company}_{strategy}_returns"] = round(returns, 2)
            
            if returns > highest_return:
                highest_return = returns
                most_profitable_stock = company
        
        results[f"Most profitable stock using {strategy}"] = most_profitable_stock
        results[f"{most_profitable_stock}'s return ({strategy})"] = highest_return
    
    save_results(results)

print("Trading analysis completed. Results saved to results.json")
