"""
初始化测试数据脚本
用于快速创建测试用户和基础数据
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.service import Service
from app.utils.security import get_password_hash


def create_test_data():
    """创建测试数据"""
    db: Session = SessionLocal()

    try:
        # 1. 创建测试用户
        print("创建测试用户...")

        # 管理员
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            mobile="13800000001",
            email="admin@petmaster.com",
            role=UserRole.ADMIN
        )
        db.add(admin)

        # 员工
        staff = User(
            username="staff",
            password_hash=get_password_hash("staff123"),
            mobile="13800000002",
            email="staff@petmaster.com",
            role=UserRole.STAFF
        )
        db.add(staff)

        # 会员
        member = User(
            username="member",
            password_hash=get_password_hash("member123"),
            mobile="13800000003",
            email="member@petmaster.com",
            role=UserRole.MEMBER
        )
        db.add(member)

        db.commit()
        print("✅ 测试用户创建成功！")

        # 2. 创建测试商品
        print("创建测试商品...")

        products = [
            Product(name="皇家狗粮", category="食品", price=299.00, stock=100),
            Product(name="猫砂", category="用品", price=89.00, stock=50),
            Product(name="宠物玩具球", category="玩具", price=29.90, stock=200),
            Product(name="宠物沐浴露", category="洗护", price=59.00, stock=80),
        ]

        for product in products:
            db.add(product)

        db.commit()
        print("✅ 测试商品创建成功！")

        # 3. 创建测试服务
        print("创建测试服务...")

        services = [
            Service(name="宠物洗澡", description="基础洗澡服务", price=80.00, duration_minutes=60),
            Service(name="宠物美容", description="专业美容造型", price=150.00, duration_minutes=120),
            Service(name="宠物体检", description="全面健康检查", price=200.00, duration_minutes=45),
            Service(name="宠物疫苗接种", description="疫苗注射服务", price=120.00, duration_minutes=30),
        ]

        for service in services:
            db.add(service)

        db.commit()
        print("✅ 测试服务创建成功！")

        print("\n" + "=" * 50)
        print("🎉 所有测试数据创建完成！")
        print("=" * 50)
        print("\n测试账号信息：")
        print("管理员 - 用户名: admin, 密码: admin123")
        print("员工   - 用户名: staff, 密码: staff123")
        print("会员   - 用户名: member, 密码: member123")
        print("\nAPI文档地址: http://localhost:8000/api/v1/docs")
        print("=" * 50)

    except Exception as e:
        print(f"❌ 创建测试数据失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成！")
    print("\n" + "=" * 50)
    create_test_data()
