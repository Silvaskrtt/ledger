# 📊 Ledger

> A comprehensive personal finance management system designed for consistency, auditability, and clarity.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-orange)]()

## 🎯 Overview

Ledger is a sophisticated personal finance management platform that combines a powerful REST API backend with an interactive web interface. It enables users to track transactions, manage budgets, monitor financial goals, and gain insights into their spending patterns with precision and clarity.

## ✨ Features

- **Transaction Management** - Record, categorize, and track all financial transactions
- **Budget Planning** - Create and monitor budgets with real-time tracking
- **Financial Goals** - Set and monitor progress towards financial objectives
- **Multi-Account Support** - Manage multiple accounts and credit cards
- **Recurring Transactions** - Automate recurring payments and income
- **Tag System** - Flexible tagging for better transaction organization
- **Analytics & Reports** - Generate insights from your financial data
- **API-First Architecture** - RESTful API for seamless integrations
- **Interactive UI** - Modern web interface with HTMX for smooth interactions

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 5.x
- **Language**: Python 3.12
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Django Authentication System
- **Real-time Updates**: Django Signals

### Frontend
- **Template Engine**: Django Templates
- **Interactivity**: HTMX
- **Styling**: Tailwind CSS
- **JavaScript**: Vanilla JS with ES6+

## 📋 Project Structure

```
ledger/
├── backend/
│   ├── accounts/           # User account management
│   ├── budgets/            # Budget management & tracking
│   ├── categories/         # Transaction categories
│   ├── config/             # Django settings & URLs
│   ├── core/               # Shared utilities & validators
│   ├── goals/              # Financial goals
│   ├── payments/           # Payment processing
│   ├── recurrence/         # Recurring transaction handling
│   ├── tags/               # Transaction tagging
│   ├── transactions/       # Core transaction logic
│   ├── users/              # User management
│   └── manage.py           # Django CLI
├── frontend/
│   ├── static/             # CSS, JavaScript, Images
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/          # HTML templates
└── requirements.txt        # Python dependencies
```

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL 12+
- pip & virtualenv

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Silvaskrtt/ledger.git
   cd ledger
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file in backend/config/
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://user:password@localhost/ledger
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000` to access the application.

## 📚 API Documentation

The API endpoints are organized by feature:

### Endpoints
- `/api/accounts/` - Account management
- `/api/budgets/` - Budget operations
- `/api/categories/` - Category management
- `/api/goals/` - Financial goals
- `/api/transactions/` - Transaction operations
- `/api/tags/` - Tag management
- `/api/payments/` - Payment processing

## 🔧 Configuration

### Database Setup
```bash
# Create database
createdb ledger

# Run migrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic --noinput
```

## 📦 Core Modules

### Accounts
Manages user account information and account-related operations.

### Budgets
Handles budget creation, updates, and real-time tracking against transactions.

### Transactions
Core transaction management with support for multiple account types.

### Goals
Financial goal setting and progress monitoring.

### Recurrence
Handles recurring transactions including scheduled payments and income.

## 🧪 Testing

```bash
# Run tests
python manage.py test

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Known Issues

Currently in active development. Check the [Issues](https://github.com/Silvaskrtt/ledger/issues) tab for known limitations and planned features.

## 📧 Support

For support, email or open an issue on the GitHub repository.

## 🙏 Acknowledgments

Built with Django and PostgreSQL. Styled with Tailwind CSS. Enhanced with HTMX.

---

**Last Updated**: January 2026 | **Status**: 🚧 Under Development
