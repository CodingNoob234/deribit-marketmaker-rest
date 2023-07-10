# deribit-marketmaker-rest
A market making algorithm based on the Avellaneda Stoikov paper on Deribit derivatives exchange. A gradient boosted model is used for volatility and directional estimates to adjust the spread and skew the quotes.

# Running the Bot
To run the market making bot, one has to create a config.py file in the root of the project.
The template is described in config_template.py
Run the application through ``` python main.py ```.