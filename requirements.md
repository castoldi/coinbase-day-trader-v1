
# objective and goal

We are starting a new coinbase crypto day trader in this folder. I have an account in coinbase but have no wallet and no api key yet, you will guide me through how to create it. The first strategy to be used in price action and get it by transcript of this youtube video: https://www.youtube.com/watch?v=HkMXGqz7MRI

# Bot Requirements

Paper trading with coinbase if possible. Does coinbase have this option?

All secrets should be stored in the .env file, create a .env.example file without the secrets. 

create a new public project under [https://github.com/castoldi](https://github.com/castoldi) for this code. Always have version control, README.MD updated for the crowd, CHANGELOG.MD and agents .md information.

in the .env have gmail passwords so you can send me emails, prefix should always have subject AI-BOT starting.

always inc version, update changelog.md and commit and push changes. Create tag for every new version. TAG should have version plus datetime in Central Time laptop time.

We need a start bot script that will keep the bot alive, I will call it every 30 mins. If bot is dead it will start, if bot is alive and healthy it will do anything. Instructions recorded in the agents and readme md files.

The bot must support multiple strategies, and we will inform during bot startup scripts which strategies to use, have an option for one or more strategies, and one option for use ALL available.

# Dashboard

Need a script to start the dashboard.  Be creative with the dashboard, surprise me.

## Live main landing page

we want a live trading view, with open trades, closed trades, PnL, win rate, coins trading, coins current price etc.

## Trading History

Should have page for  trading history. 

## Account Management

The bot will be given a $1000 dollars to trade. It should rollover the account cash available. Example: if first day bot loses $200, then next day it should know it has only $800 to trade. If bot wins $300 in the first day, second day it will have 1300 to trade. If it loses 50% of the initial $1000 bot should stop forever until I manually reallow it to trade.

## Backtests

All back tests runs are recorded in a Backtests page.

Backtests landing page should contain a summary of all backtests combined.

for every period of backtest, start with $1000 cash.

Always run backtests for 2024, 2025, 2026 and Last 30 days.

Download market data for main coins since 2024 and store in this folder so it can be reused.

Security first, never commit and push secrets.

It is ok to push market data to github.

## Strategy page

Create a page in the describing the strategies with 2 candle charts examples for each strategy. Entry points. Stop loss, take profit etc.

# AI Generic Instructions File
Create a generic instruction files with these info necessary for AI to understand what to do with this code and how.

# Logs
Bot and dashboard should have separated files under logs/ folder. 

The logs should rotate, keep 7 days of logs, one per day, compress logs that rolled over.

# Readme.md
The readme.md file should have information what is this bot, disclaimer that I am not a financial professional and etc.
readme.md should have screenshots of the dashboard.
it should have information about all strategies and a text with the backtest information.