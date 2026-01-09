from datetime import date
from sqlmodel import select, text
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.product import Product
from app.models.staff import Staff
from app.models.supplier import Supplier
from app.models.inbound_order import InboundDetail, InboundOrder
from app.models.warehouse import Warehouse
from app.models.requisition import Requisition, ReqDetail

# --- Seed Staff ---
INITIAL_STAFF = [
    {"StaffID": 1, "stName": "Admin", "stDept": "管理部"},
    {"StaffID": 2, "stName": "張倉管", "stDept": "倉庫部"},
    {"StaffID": 3, "stName": "李採購", "stDept": "採購部"},
]

# --- Seed Supplier ---
INITIAL_SUPPLIERS = [
    {"SupplierID": 1, "suName": "A公司", "suPhone": "02-2345-6789", "suAddress": "台北市信義區..."},
    {"SupplierID": 2, "suName": "B公司", "suPhone": "04-8765-4321", "suAddress": "台中市西屯區..."},
]

# --- Seed Product ---
INITIAL_PRODUCTS = [
    {"ProductID": 1, "prName": "無線耳機", "prSpec": "藍牙 5.0", "prCategory": "電子產品"},
    {"ProductID": 2, "prName": "機械鍵盤", "prSpec": "青軸", "prCategory": "電腦周邊"},
    {"ProductID": 3, "prName": "電競滑鼠", "prSpec": "DPI 16000", "prCategory": "電腦周邊"},
]

# --- Seed Warehouse ---
INITIAL_WAREHOUSES = [
    {"WarehouseID": 101, "waName": "一號倉", "waLocation": "台北總部 B1"},
    {"WarehouseID": 102, "waName": "二號倉", "waLocation": "台中物流中心"},
    {"WarehouseID": 103, "waName": "冷凍倉", "waLocation": "桃園觀音"},
]

# --- Seed InboundOrder ---
INITIAL_INBOUNDS = [
    {
        "InboundID": 1, "ioDate": date(2025, 12, 1), "SupplierID": 1, "StaffID": 2,
        "details": [
            {"ProductID": 1, "idQuantity": 50, "WarehouseID": 101},
            {"ProductID": 2, "idQuantity": 20, "WarehouseID": 101},
        ]
    }
]

# --- Seed Requisition ---
INITIAL_REQUISITIONS = [
    {
        "ReqID": 1, "reDate": date(2025, 12, 2), "reReason": "產線領料", "StaffID": 2,
        "details": [
            {"ProductID": 1, "rdQuantity": 10, "WarehouseID": 101},
            {"ProductID": 2, "rdQuantity": 5, "WarehouseID": 101},
        ]
    }
]

async def create_initial_data(db: AsyncSession):
    result = await db.exec(select(Staff))
    first_staff = result.first()
    
    if not first_staff:
        print("🌱 Seeding Staff data...")
        for data in INITIAL_STAFF:
            staff = Staff(
                StaffID=data["StaffID"], 
                stName=data["stName"], 
                stDept=data["stDept"]
            )
            db.add(staff)
        await db.commit()


    result = await db.exec(select(Supplier))
    if not result.first():
        print("🌱 Seeding Supplier data...")
        for data in INITIAL_SUPPLIERS:
            supplier = Supplier(**data) # 使用 unpacking 快速賦值
            db.add(supplier)
        await db.commit()
    
    result = await db.exec(select(Product))
    if not result.first():
        print("🌱 Seeding Product data...")
        for data in INITIAL_PRODUCTS:
            product = Product(**data)
            db.add(product)
        await db.commit()

    result = await db.exec(select(Warehouse))
    if not result.first():
        print("🌱 Seeding Warehouse data...")
        for data in INITIAL_WAREHOUSES:
            db.add(Warehouse(**data))
        await db.commit()

    result = await db.exec(select(InboundOrder))
    if not result.first():
        print("🌱 Seeding InboundOrder data...")
        for data in INITIAL_INBOUNDS:
            details_data = data.pop("details")
            order = InboundOrder(**data)
            db.add(order)

            for d in details_data:
                detail = InboundDetail(InboundID=order.InboundID, **d)
                db.add(detail)
        
        await db.commit()

    result = await db.exec(select(Requisition))
    if not result.first():
        print("🌱 Seeding Requisition data...")
        for data in INITIAL_REQUISITIONS:
            # 1. 取出明細資料
            details_data = data.pop("details")
            
            # 2. 建立主單
            req = Requisition(**data)
            db.add(req)
            # 因為我們有手動指定 ReqID，所以可以直接 add details
            
            # 3. 建立明細
            for d in details_data:
                detail = ReqDetail(ReqID=req.ReqID, **d)
                db.add(detail)
        
        await db.commit()

    try:
        # 1. 重置 Staff
        await db.exec(text("SELECT setval(pg_get_serial_sequence('staff', 'StaffID'), (SELECT MAX(\"StaffID\") FROM staff));"))
        
        # 2. 重置 Supplier
        await db.exec(text("SELECT setval(pg_get_serial_sequence('supplier', 'SupplierID'), (SELECT MAX(\"SupplierID\") FROM supplier));"))
        
        # 3. 重置 Product
        await db.exec(text("SELECT setval(pg_get_serial_sequence('product', 'ProductID'), (SELECT MAX(\"ProductID\") FROM product));"))

        # 4. 重置 Warehouse
        await db.exec(text("SELECT setval(pg_get_serial_sequence('warehouse', 'WarehouseID'), (SELECT MAX(\"WarehouseID\") FROM warehouse));"))

        # 5. 重置 InboundOrder
        await db.exec(text("SELECT setval(pg_get_serial_sequence('inboundorder', 'InboundID'), (SELECT MAX(\"InboundID\") FROM inboundorder));"))
        
        # 6. 重置 Requisition
        await db.exec(text("SELECT setval(pg_get_serial_sequence('requisition', 'ReqID'), (SELECT MAX(\"ReqID\") FROM requisition));"))

        # 🔥 關鍵修正：必須 Commit 才會生效！
        await db.commit() 
        print("🔄 PostgreSQL Sequences have been reset.")
        
    except Exception as e:
        print(f"ℹ️ Sequence reset skipped: {e}")