# deribit-marketmaker-rest
A market making algorithm based on the Avellaneda Stoikov paper on Deribit derivatives exchange. A gradient boosted model is used for volatility and directional estimates to adjust the spread and skew the quotes. 

It is important to note that this bot with current configuration is unprofitable. I found this to be largely caused by toxic fills by not monitoring trading data from other exchanges.

# Running the Bot
The project contains everything you need to run the bot, including pre-trained models. 
To run the market making bot, one has to create a config.py file in the root of the project.
The template is described in config_template.py
Run the application through ``` python marketmaking_bot.py ```.

# Development Iteration
## Getting data
Running ``` python request_data.py ``` starts an infinite loop that request the orderbook with depth 20 and publicly excecuted trades, for a specified interval. If the dataframe becomes too large, it is stored as a file and a new empty dataframe is created.
Improvements can be made by running the script in a docker container and inserting each new query in a SQL database for example.

## Preprocessing data to features
Running ``` python process_data.py ``` loads the files that are stored under the path specified in request_data.py.
The processed features are stored in the path. It is important that this file contains the best bid/ask and executed volume as well. This is important because this data is used in the backtesting.

## Training volatility and directional models
To train the models, execute both model_direction_regr.ipynb and model_volatility.ipynb. These will load the processed features computed above, train a lightgbm model and save the model using pickle.

## Backtesting the strategy
Again load the processed features. Select the strategy from strategy.ipynb and define the machine learning model. Run the code and test for multiple parameters.

## Deploying the strategy
In marketmaking_bot.py, define again the model to use and strategy to compute the quotes with.
