# 👓 OptiFlow AI

***AI Powered Order Management System for Eyewear Brand***

OptiFlow AI is an intelligent order management system designed specifically for eyewear brands. It handles the complete order lifecycle—from prescription intake to delivery—with AI assisting at key stages including inventory checking, SLA prediction, QC failure forecasting, and breach alerting.

---

## 📋 Objective

Build a working AI-powered order management system for an eyewear brand that handles the full order lifecycle, from intake to delivery, with AI assisting at key stages.

### Key Challenges Addressed

* **Complex Orders**: Each order carries a prescription, lens type, lens index, coating, and frame
* **Multi-source Orders**: Orders come from multiple sources (website, stores, partners)
* **Complex Fulfillment**: Multiple stages from order placed to delivered
* **Different SLAs**: Each lens type has different SLA (Service Level Agreement)
* **QC Failure Loops**: Failures at QC loop back to re-order

---

## 🚀 Features

### 1. Lens Inventory Management

* Check if prescription power is in-house or needs vendor sourcing
* Real-time inventory availability check at order placement
* Automatic SLA adjustment based on stock availability
* AI-powered reorder recommendations

### 2. Order Dashboard

* Unified dashboard for team to manage all orders
* Real-time order tracking through all stages
* Filterable by status, lens type, and store location
* Update order status and log delay reasons
* Color-coded risk indicators (Green/Yellow/Red)

### 3. TAT Prediction & Breach Alerts

* AI predicts which orders are likely to breach SLA before it happens
* Continuous monitoring of active orders (hourly)
* Risk score calculation (0–1 scale)
* Automated alerts via Email and WhatsApp
* Proactive team notifications 24–48 hours before breach

### 4. Order Lifecycle Stages

Order Placed → Prescription Check → Lens Sourcing
Cutting & Edging → Coating → QC → Packing
Dispatched → Delivered

### 5. User Roles

| Role              | Permissions                                                   |
| ----------------- | ------------------------------------------------------------- |
| **Admin**         | Full access: manage inventory, view all orders, configure SLA |
| **Customer**      | Create orders, view own orders, track progress                |
| **Store Manager** | View store orders, update status, log delays                  |
| **QC Inspector**  | View QC stage orders, record pass/fail results                |

---

## 🛠️ Tech Stack

### Backend

| Technology            | Purpose                     |
| --------------------- | --------------------------- |
| Python 3.11           | Programming language        |
| FastAPI               | REST API framework          |
| SQLAlchemy            | ORM for database operations |
| PostgreSQL (Supabase) | Database                    |
| JWT                   | Authentication              |
| bcrypt                | Password hashing            |

### Frontend

| Technology | Purpose                   |
| ---------- | ------------------------- |
| Streamlit  | Web application framework |
| Requests   | HTTP client               |
| Pandas     | Data manipulation         |

### Deployment

| Technology          | Purpose             |
| ------------------- | ------------------- |
| Docker              | Containerization    |
| Hugging Face Spaces | Deployment platform |

### AI/ML

| Technology           | Purpose               |
| -------------------- | --------------------- |
| Rule-based AI        | SLA breach prediction |
| Time-series analysis | TAT prediction        |
| Pattern matching     | QC failure prediction |

---

## 📦 Setup

### Prerequisites

* Python 3.12+
* PostgreSQL
* Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/acrobyte007/OptiFlow-AI
cd OptiFlow-AI
```

---

### 2. Backend Setup

#### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create `.env` file:

```env
DB_URL=postgresql+asyncpg://user:password@host:5432/db_name
SECRET_KEY=your-secret-key
ADMIN_SECRET_KEY=your-admin-secret-key
BACKEND_URL=https://your-backend-url.hf.space
```

#### Run Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:<http://localhost:8000>

---

### 3. Frontend Setup

```bash
pip install -r requirements-frontend.txt
```

#### Run Frontend

```bash
streamlit run app.py
```

Frontend: <http://localhost:8501>

---

### 4. Docker Deployment (Hugging Face Spaces)

#### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PORT=7860

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

#### Frontend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-frontend.txt .
RUN pip install --no-cache-dir -r requirements-frontend.txt

COPY app_frontend.py .

EXPOSE 7860

ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

CMD ["streamlit", "run", "app_frontend.py"]
```

---

## 📁 Project Structure

``` bash
optiflow-ai/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── api/
│   │   ├── users.py
│   │   ├── order.py
│   │   └── sla_store.py
│   ├── features/
│   └── utils/
├── app_frontend.py
├── requirements.txt
├── requirements-frontend.txt
├── Dockerfile
├── .env
└── README.md
```

---

## 🔌 API Endpoints

### Authentication

* POST `/api/user/register`
* POST `/api/user/login`
* GET `/api/user/me`

### Orders

* POST `/api/orders/create`
* GET `/api/orders/my`
* GET `/api/orders/{id}`

### Admin

* GET `/api/orders/admin/all`
* PATCH `/api/store/orders/{id}/status`

### Inventory

* POST `/api/store/lens/add`
* POST `/api/store/inventory/add`
* PUT `/api/store/inventory/{id}`
* GET `/api/store/inventory/all`

### SLA

* POST `/api/store/sla/set`
* GET `/api/store/sla/all`

---

## 🧪 Testing

### Login

```bash
curl -X POST http://localhost:8000/api/user/login \
-H "Content-Type: application/json" \
-d '{"email": "john@example.com", "password": "password123"}'
```

### Create Order

```bash
curl -X POST http://localhost:8000/api/orders/create \
-H "Authorization: Bearer YOUR_TOKEN" \
-d '{...}'
```

---

## 📊 Database Schema

Core Tables:

* users
* customers
* orders
* prescriptions
* lenses
* inventory
* order_logs
* qc
* sla_config
* store_delay_config
* stage_time_config

---

## 🔗 Links

* Backend: <https://ajoy0071998-optiflow.hf.space>
* Frontend: <https://ajoy0071998-optiflow-frontend.hf.space>

---

## 🙏 Acknowledgments

* Hugging Face Spaces
