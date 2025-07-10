from db import Base, engine

# Удаляем все таблицы
Base.metadata.drop_all(bind=engine)
print("Все таблицы удалены.")

# Создаем все таблицы заново
Base.metadata.create_all(bind=engine)
print("Все таблицы созданы заново.")