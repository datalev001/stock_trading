import pandas as pd
import numpy as np

def turtle_trading(DF, first_date):
    # Convert first_date string to datetime
    first_date = pd.to_datetime(first_date)
    DF['Date'] = pd.to_datetime(DF['Date'])
    
    # Filter DataFrame from the starting date
    DF = DF[DF['Date'] >= first_date].reset_index(drop=True)
    
    # Turtle Trading Logic
    window = 20
    initial_capital = 10000
    DF_trade = pd.DataFrame(columns=['Date', 'action', 'dollar_amount', 'price'])
    holding = False
    buy_price = 0
    sell_price = 0
    buy_date = None
    
    for i in range(window, len(DF)):
        
        current_date = DF.iloc[i]['Date']
        high_breakout = DF.iloc[i-window:i]['Close'].max()
        low_breakout = DF.iloc[i-window:i]['Close'].min()
                
        
        if not holding and DF.iloc[i]['Close'] > high_breakout:
            # Buy signal
            holding = True
            buy_price = DF.iloc[i]['Close']
            buy_date = current_date
            DF_trade = DF_trade.append({'Date': current_date, 'action': 'buy', 'dollar_amount': initial_capital, 'price' : DF.iloc[i]['Close']}, ignore_index=True)
        elif holding:
            sell_condition = (DF.iloc[i]['Close'] < low_breakout or
                               (DF.iloc[i]['Close'] <= buy_price * 0.97) or
                               (current_date - buy_date).days >= 10)
            
            if sell_condition:
                # Sell signal
                holding = False
                sell_price = DF.iloc[i]['Close']
                sell_amount = initial_capital * (sell_price / buy_price)
                initial_capital = sell_amount  # Update capital after the trade
                DF_trade = DF_trade.append({'Date': current_date, 'action': 'sell', 'dollar_amount': sell_amount, 'price' : DF.iloc[i]['Close']}, ignore_index=True)
                buy_price = 0  # Reset buy price for next trade
                buy_date = None
    
    # If holding stock at the end of the period, sell it
    if holding:
        sell_price = DF.iloc[len(DF)-1]['Close']
        sell_amount = initial_capital * (sell_price / buy_price)
        DF_trade = DF_trade.append({'Date': DF.iloc[len(DF)-1]['Date'], 'action': 'sell', 'dollar_amount': sell_amount, 'price': DF.iloc[len(DF)-1]['Close']}, ignore_index=True)
    
    return DF_trade

###relax rule
def boll_rsi_relaxed(DF):
    # Calculate Bollinger Bands
    rolling_mean = DF['Close'].rolling(window=20).mean()
    rolling_std = DF['Close'].rolling(window=20).std()
    DF['UpperBB'] = rolling_mean + (rolling_std * 2)
    DF['LowerBB'] = rolling_mean - (rolling_std * 2)
    
    # Calculate RSI
    delta = DF['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    RS = gain / loss
    DF['RSI'] = 100 - (100 / (1 + RS))
    
    # Trading signals
    DF_trade = pd.DataFrame(columns=['Date', 'action', 'price'])
    holding = False
    
    for i in range(1, len(DF)):
        # Relaxed Buy conditions
        price = DF.iloc[i]['Close']
        if not holding and (DF.iloc[i]['Close'] < DF.iloc[i]['LowerBB'] * 1.02 and DF.iloc[i]['RSI'] < 40):  # Adjusted thresholds
            DF_trade = DF_trade.append({'Date': DF.iloc[i]['Date'], 'action': 'buy', 'price': price}, ignore_index=True)
            holding = True
        
        # Relaxed Sell conditions
        elif holding and (DF.iloc[i]['Close'] > DF.iloc[i]['UpperBB'] * 0.98 or DF.iloc[i]['RSI'] > 60):  # Adjusted thresholds
            DF_trade = DF_trade.append({'Date': DF.iloc[i]['Date'], 'action': 'sell', 'price': price}, ignore_index=True)
            holding = False
    
    return DF_trade

# Example usage (replace DF with your actual DataFrame)
DF_trade1 = boll_rsi_relaxed(DF)
print(DF_trade1)
##################################
def buy_hold_sell(DF):
    # Buy and hold logic function
    buy_price = DF.iloc[0]['Close']
    sell_price = DF.iloc[-1]['Close']
    gain = 10000 * (sell_price - buy_price) / buy_price
    return gain

########################

stocks = ['XLE' , 'XLF', 'XLV', 'XLK', 'XLU', 'XLY', 'VIG', 'GLD', 'SPY', 'DIA']
stcks_DF = fetch_stock_byday(stocks, '2020-10-01', '2024-02-20')
stcks_DF = stcks_DF.sort_values(['Date'])

def eva_stocks(stcks_DF, stocks, eve_st_tm, eve_ed_tm):
    res_df = pd.DataFrame(columns=['stock', 'turtle', 'rsi_boll', 'buy_hold_sell'])
    detail_df = pd.DataFrame(columns=['stock', 'action', 'transaction_price', 'trading_method'])

    for stock in stocks:
        # Extract data for the current stock within the evaluation period
        stock_data = stcks_DF[(stcks_DF['ticker'] == stock) & (stcks_DF['Date'] >= eve_st_tm) & (stcks_DF['Date'] <= eve_ed_tm)].reset_index(drop=True)
        
        # Turtle Trading
        turtle_result = turtle_trading(stock_data, eve_st_tm)
        turtle_gain = 10000 * (turtle_result['price'].iloc[-1] - turtle_result['price'].iloc[0]) / turtle_result['price'].iloc[0]
        
        # Bollinger Bands and RSI
        boll_rsi_result = boll_rsi_relaxed(stock_data)
        boll_rsi_gain = 10000 * (boll_rsi_result['price'].iloc[-1] - boll_rsi_result['price'].iloc[0]) / boll_rsi_result['price'].iloc[0]
        
        # Buy and Hold
        buy_hold_gain = buy_hold_sell(stock_data)
        
        # Store gains in res_df
        res_df = res_df.append({'stock': stock, 'turtle': turtle_gain, 'rsi_boll': boll_rsi_gain, 'buy_hold_sell': buy_hold_gain}, ignore_index=True)
        
        # Store transaction details in detail_df
        detail_df = pd.concat([detail_df, turtle_result.assign(stock=stock, trading_method='turtle'),
                               boll_rsi_result.assign(stock=stock, trading_method='rsi_boll')])
        detail_df = detail_df.append({'stock': stock, 'action': 'buy', 'transaction_price': stock_data.iloc[0]['Close'], 'trading_method': 'buy_hold_sell'}, ignore_index=True)
        detail_df = detail_df.append({'stock': stock, 'action': 'sell', 'transaction_price': stock_data.iloc[-1]['Close'], 'trading_method': 'buy_hold_sell'}, ignore_index=True)

    return res_df, detail_df

# Example usage:
## 1 bear and two bull    
res_202011_202402, detail_df = eva_stocks(stcks_DF, ['XLE', 'XLF', 'XLV', 'XLK', 'XLU', 'XLY', 'VIG', 'GLD', 'SPY', 'DIA'], '2020-11-15', '2024-02-20')
print(res_202011_202402)
print(detail_df)
res_202011_202402.to_excel('stock_market_indicator_history_check\res_202011_202402.xlsx', index = False)

