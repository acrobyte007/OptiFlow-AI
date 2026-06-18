import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# API Configuration
API_BASE_URL = "https://ajoy0071998-optiflow-ai.hf.space/"

# Page Configuration
st.set_page_config(
    page_title="OptiFlow AI",
    page_icon="👓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Session State Initialization
# ============================================================
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ============================================================
# Helper Functions
# ============================================================
def api_request(method, endpoint, data=None, headers=None):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return None
        
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please make sure the backend is running.")
        return None

def login(email, password):
    """Login user"""
    response = api_request("POST", "/api/user/login", {"email": email, "password": password})  # ✅ Changed
    if response and response.status_code == 200:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.user = data["user"]
        st.session_state.role = data["user"]["role"]
        return True
    return False

def logout():
    """Logout user"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

def register_user(name, email, password, role, store_location):
    """Register new user"""
    response = api_request("POST", "/api/user/register", {  # ✅ Changed
        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "store_location": store_location
    })
    return response

def create_order(store_location, lens_type, lens_index, coating, frame_model, prescription):
    """Create new order"""
    response = api_request("POST", "/api/orders/create", {
        "store_location": store_location,
        "lens_type": lens_type,
        "lens_index": lens_index,
        "coating": coating,
        "frame_model": frame_model,
        "prescription": prescription
    })
    return response

def get_my_orders(status=None, page=1, limit=20):
    """Get customer orders"""
    params = f"?page={page}&limit={limit}"
    if status:
        params += f"&status={status}"
    response = api_request("GET", f"/api/orders/my{params}")
    return response

def get_all_orders(status=None, store=None, page=1, limit=20):
    """Get all orders (admin only)"""
    params = f"?page={page}&limit={limit}"
    if status:
        params += f"&status={status}"
    if store:
        params += f"&store={store}"
    response = api_request("GET", f"/api/orders/admin/all{params}")
    return response

def get_order_by_id(order_id):
    """Get order by ID"""
    response = api_request("GET", f"/api/orders/{order_id}")
    return response

def update_order_status(order_id, status, delay_reason=None):
    """Update order status (admin only)"""
    response = api_request("PATCH", f"/api/store/orders/{order_id}/status", {
        "status": status,
        "delay_reason": delay_reason
    })
    return response

def get_inventory_all():
    """Get all inventory (admin only)"""
    response = api_request("GET", "/api/store/inventory/all")
    return response

def add_inventory(lens_type, lens_index, coating, power, quantity, location):
    """Add inventory (admin only)"""
    response = api_request("POST", "/api/store/inventory/add", {
        "lens_type": lens_type,
        "lens_index": lens_index,
        "coating": coating,
        "power": power,
        "quantity": quantity,
        "location": location
    })
    return response

def get_sla_configs():
    """Get all SLA configurations (admin only)"""
    response = api_request("GET", "/api/store/sla/all")
    return response

def set_sla(lens_type, sla_hours, complexity_factor, store_delay_hours):
    """Set SLA for lens type (admin only)"""
    response = api_request("POST", "/api/store/sla/set", {
        "lens_type": lens_type,
        "sla_hours": sla_hours,
        "complexity_factor": complexity_factor,
        "store_delay_hours": store_delay_hours
    })
    return response

# ============================================================
# Authentication Pages
# ============================================================
def login_page():
    """Login page"""
    st.title("👓 OptiFlow AI")
    st.subheader("Login to your account")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if login(email, password):
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid email or password")
    
    st.divider()
    st.write("Don't have an account?")
    if st.button("Register Here"):
        st.session_state.page = "register"
        st.rerun()

def register_page():
    """Registration page"""
    st.title("👓 OptiFlow AI")
    st.subheader("Create a new account")
    
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["CUSTOMER", "STORE_MANAGER", "QC_INSPECTOR", "WAREHOUSE", "SUPPORT"])
        store_location = st.text_input("Store Location (optional)", "")
        
        submit = st.form_submit_button("Register")
        
        if submit:
            response = register_user(name, email, password, role, store_location)
            if response and response.status_code == 200:
                st.success("✅ Registration successful! Please login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(f"❌ Registration failed: {response.json().get('detail', 'Unknown error') if response else 'Server error'}")
    
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# ============================================================
# Dashboard Pages
# ============================================================
def customer_dashboard():
    """Customer dashboard"""
    st.title("👓 My Orders")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "PLACED", "PROCESSING", "QC", "DISPATCHED", "DELIVERED"])
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Orders"):
            st.rerun()
    
    status = None if status_filter == "All" else status_filter
    response = get_my_orders(status)
    
    if response and response.status_code == 200:
        data = response.json()
        orders = data.get("orders", [])
        total = data.get("total", 0)
        
        st.info(f"📊 Total Orders: {total}")
        
        if orders:
            for order in orders:
                with st.expander(f"Order #{order['id'][:8]} - {order['status']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Store:** {order['store_location']}")
                        st.write(f"**Status:** `{order['status']}`")
                        st.write(f"**Progress:** {order['progress_percentage']}%")
                    with col2:
                        st.write(f"**Created:** {order['created_at'][:16]}")
                        st.write(f"**SLA Deadline:** {order['sla_deadline'][:16]}")
                        st.write(f"**Estimated Arrival:** {order['estimated_arrival'][:16]}")
                    with col3:
                        st.write(f"**Risk Score:** {order['risk_score']:.2f}")
                        st.write(f"**Breached:** {'✅ No' if not order['is_breached'] else '❌ Yes'}")
                        if st.button(f"View Details", key=f"view_{order['id']}"):
                            st.session_state.view_order = order['id']
                            st.rerun()
        else:
            st.info("No orders found. Create your first order!")
    else:
        st.error("Failed to fetch orders")
    
    # Order creation section
    st.divider()
    st.subheader("📦 Create New Order")
    
    with st.form("create_order_form"):
        col1, col2 = st.columns(2)
        with col1:
            store_location = st.selectbox("Store Location", ["NYC Store", "LA Store", "Chicago Store", "Online Store"])
            lens_type = st.selectbox("Lens Type", ["Single Vision", "Progressive", "High Index", "Bifocal", "Standard"])
            lens_index = st.selectbox("Lens Index", [1.5, 1.56, 1.6, 1.67, 1.74])
            coating = st.selectbox("Coating", ["None", "Anti-glare", "Blue Cut", "Hydrophobic"])
            frame_model = st.text_input("Frame Model (optional)", "")
        
        with col2:
            st.write("Prescription")
            sph = st.number_input("SPH", min_value=-20.0, max_value=20.0, step=0.25, value=-2.50)
            cyl = st.number_input("CYL (optional)", min_value=-10.0, max_value=10.0, step=0.25, value=0.0)
            axis = st.number_input("Axis (optional)", min_value=0, max_value=180, step=1, value=180)
            add_power = st.number_input("Add Power (optional)", min_value=0.0, max_value=5.0, step=0.25, value=0.0)
        
        coating_val = None if coating == "None" else coating
        frame_val = None if frame_model == "" else frame_model
        
        submit = st.form_submit_button("📦 Create Order")
        
        if submit:
            prescription = {
                "sph": sph,
                "cyl": cyl if cyl != 0 else None,
                "axis": axis if axis != 0 else None,
                "add_power": add_power if add_power != 0 else None
            }
            
            response = create_order(
                store_location, lens_type, lens_index,
                coating_val, frame_val, prescription
            )
            
            if response and response.status_code == 200:
                st.success(f"✅ Order created successfully! Order ID: {response.json()['id']}")
                st.rerun()
            else:
                st.error(f"❌ Failed to create order: {response.json().get('detail', 'Unknown error') if response else 'Server error'}")

def admin_dashboard():
    """Admin dashboard"""
    st.title("👓 Admin Dashboard")
    
    tabs = st.tabs(["📦 Orders", "📊 Inventory", "⚙️ Settings"])
    
    # ============================================================
    # Orders Tab
    # ============================================================
    with tabs[0]:
        st.subheader("All Orders")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "PLACED", "PROCESSING", "QC", "DISPATCHED", "DELIVERED"])
        with col2:
            store_filter = st.selectbox("Filter by Store", ["All", "NYC Store", "LA Store", "Chicago Store", "Online Store"])
        with col3:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh"):
                st.rerun()
        
        status = None if status_filter == "All" else status_filter
        store = None if store_filter == "All" else store_filter
        
        response = get_all_orders(status, store)
        
        if response and response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            total = data.get("total", 0)
            
            st.info(f"📊 Total Orders: {total}")
            
            if orders:
                for order in orders:
                    with st.expander(f"Order #{order['id'][:8]} - {order['status']} - {order['customer_name']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Customer:** {order['customer_name']}")
                            st.write(f"**Store:** {order['store_location']}")
                            st.write(f"**Status:** `{order['status']}`")
                        with col2:
                            st.write(f"**Created:** {order['created_at'][:16]}")
                            st.write(f"**SLA Deadline:** {order['sla_deadline'][:16]}")
                            st.write(f"**Breached:** {'✅ No' if not order['is_breached'] else '❌ Yes'}")
                        with col3:
                            new_status = st.selectbox(
                                "Update Status",
                                ["PLACED", "PROCESSING", "QC", "DISPATCHED", "DELIVERED"],
                                key=f"status_{order['id']}"
                            )
                            delay_reason = st.text_input("Delay Reason (optional)", key=f"delay_{order['id']}")
                            if st.button(f"Update", key=f"update_{order['id']}"):
                                response = update_order_status(order['id'], new_status, delay_reason)
                                if response and response.status_code == 200:
                                    st.success("✅ Status updated!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update status")
            else:
                st.info("No orders found")
        else:
            st.error("Failed to fetch orders")
    
    # ============================================================
    # Inventory Tab
    # ============================================================
    with tabs[1]:
        st.subheader("📊 Inventory Management")
        
        # Add inventory form
        with st.expander("➕ Add Inventory"):
            with st.form("add_inventory_form"):
                col1, col2 = st.columns(2)
                with col1:
                    inv_lens_type = st.selectbox("Lens Type", ["Single Vision", "Progressive", "High Index", "Bifocal", "Standard"])
                    inv_lens_index = st.selectbox("Lens Index", [1.5, 1.56, 1.6, 1.67, 1.74])
                    inv_coating = st.selectbox("Coating", ["None", "Anti-glare", "Blue Cut", "Hydrophobic"])
                with col2:
                    inv_power = st.number_input("Power", min_value=-20.0, max_value=20.0, step=0.25, value=-2.50)
                    inv_quantity = st.number_input("Quantity", min_value=1, value=50)
                    inv_location = st.text_input("Location", "NYC Warehouse")
                
                coating_val = None if inv_coating == "None" else inv_coating
                
                if st.form_submit_button("Add Inventory"):
                    response = add_inventory(inv_lens_type, inv_lens_index, coating_val, inv_power, inv_quantity, inv_location)
                    if response and response.status_code == 200:
                        st.success("✅ Inventory added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add inventory")
        
        # Display inventory
        response = get_inventory_all()
        if response and response.status_code == 200:
            inventory = response.json()
            if inventory:
                df = pd.DataFrame(inventory)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No inventory found")
        else:
            st.error("Failed to fetch inventory")
    
    # ============================================================
    # Settings Tab
    # ============================================================
    with tabs[2]:
        st.subheader("⚙️ SLA Configuration")
        
        # Set SLA form
        with st.expander("Set SLA"):
            with st.form("set_sla_form"):
                lens_type = st.selectbox("Lens Type", ["Single Vision", "Progressive", "High Index", "Bifocal", "Standard"])
                sla_hours = st.number_input("SLA Hours", min_value=1, max_value=720, value=168)
                complexity_factor = st.number_input("Complexity Factor", min_value=0.5, max_value=3.0, step=0.1, value=1.5)
                store_delay_hours = st.number_input("Store Delay Hours", min_value=0, max_value=168, value=24)
                
                if st.form_submit_button("Set SLA"):
                    response = set_sla(lens_type, sla_hours, complexity_factor, store_delay_hours)
                    if response and response.status_code == 200:
                        st.success("✅ SLA configured successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to set SLA")
        
        # Display current SLA configs
        response = get_sla_configs()
        if response and response.status_code == 200:
            configs = response.json()
            if configs:
                df = pd.DataFrame(configs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No SLA configurations found")
        else:
            st.error("Failed to fetch SLA configurations")

# ============================================================
# Main App
# ============================================================
def main():
    # Sidebar
    with st.sidebar:
        st.title("👓 OptiFlow AI")
        
        if st.session_state.user:
            st.write(f"**User:** {st.session_state.user['name']}")
            st.write(f"**Role:** `{st.session_state.role}`")
            st.write(f"**Email:** {st.session_state.user['email']}")
            
            st.divider()
            
            if st.button("🚪 Logout"):
                logout()
    
    # Page routing
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    if not st.session_state.token:
        if st.session_state.page == "register":
            register_page()
        else:
            login_page()
    else:
        if st.session_state.role == "ADMIN":
            admin_dashboard()
        else:
            customer_dashboard()

if __name__ == "__main__":
    main()