.PHONY: test scan backtest paper-trade dashboard

test:
	python -m pytest tests/ -v

scan:
	python -m stockmarket.main scan --limit 10

backtest:
	python -m stockmarket.main backtest --ticker $(or $(TICKER),AAPL) --period 5y

paper-trade:
	python -m stockmarket.main paper-trade --limit 10

dashboard:
	python -m stockmarket.main dashboard