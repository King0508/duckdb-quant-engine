# Contributing to Quantitative Finance SQL Warehouse

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/quant-sql-warehouse.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
5. Install dependencies: `pip install -r requirements.txt`

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding tests

### 2. Make Changes

- Write clean, readable code
- Follow PEP 8 style guidelines
- Add docstrings to functions and classes
- Update tests as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_etl.py -v
```

### 4. Code Quality

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add new analytics function for momentum indicators"
```

Commit message format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- Clear title and description
- Reference any related issues
- Include test results
- Request review from maintainers

## Code Standards

### Python Style

- Follow PEP 8
- Maximum line length: 120 characters
- Use type hints where appropriate
- Write comprehensive docstrings

Example:

```python
def calculate_returns(prices: pd.Series, periods: int = 1) -> pd.Series:
    """
    Calculate percentage returns over specified periods.

    Args:
        prices: Series of prices
        periods: Number of periods for return calculation

    Returns:
        Series of percentage returns
    """
    return prices.pct_change(periods) * 100
```

### SQL Style

- Use uppercase for SQL keywords
- Indent subqueries and clauses
- Use meaningful table aliases
- Add comments for complex logic

Example:

```sql
-- Calculate daily returns with RSI
SELECT
    s.ticker,
    b.ts,
    b.close,
    -- Daily return calculation
    (b.close - LAG(b.close, 1) OVER w) / LAG(b.close, 1) OVER w * 100 AS return_pct
FROM bars b
JOIN symbols s ON b.symbol_id = s.symbol_id
WINDOW w AS (PARTITION BY b.symbol_id ORDER BY b.ts)
ORDER BY b.ts DESC
```

### Testing

- Write tests for new features
- Aim for >80% code coverage
- Use descriptive test names
- Include edge cases

Example:

```python
def test_calculate_returns_with_valid_data():
    """Test returns calculation with valid price data."""
    prices = pd.Series([100, 105, 103, 107])
    returns = calculate_returns(prices)

    assert len(returns) == 4
    assert returns.iloc[1] == pytest.approx(5.0)
```

## Project Structure

```
quant-sql-warehouse/
├── etl/              # ETL scripts
├── sql/              # SQL schemas and views
├── api/              # REST API
├── analytics/        # Analysis scripts
├── tests/            # Test suite
├── data/             # Data files
└── docs/             # Documentation
```

## Adding New Features

### 1. New Data Sources

To add a new data source:

1. Update `sql/schema.sql` with new tables
2. Add generator logic to `etl/generate_data.py`
3. Update `etl/load_data.py` to load new data
4. Add validation in `etl/data_validator.py`
5. Create tests

### 2. New Analytics

To add new analytical views:

1. Create SQL file in `sql/views/`
2. Add view creation to `etl/load_data.py`
3. Create query functions in `analytics/run_analysis.py`
4. Add API endpoints in `api/main.py`
5. Write tests

### 3. New API Endpoints

To add new endpoints:

1. Add route function in `api/main.py`
2. Follow FastAPI best practices
3. Include parameter validation
4. Add comprehensive tests
5. Update API documentation

## Reporting Issues

When reporting issues, include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Error messages and stack traces

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Review documentation

Thank you for contributing! 🚀
