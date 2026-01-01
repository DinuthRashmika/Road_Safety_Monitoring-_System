# # ----Database initialization
# # wraps the database we are interating with
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# from config.config import settings

# engine = create_engine(
#     settings.DATABASE_URL
# )

# SessionLocal = sessionmaker(autocommit=False, autoFlush=False, bind=engine)

# # All the models can inherit from the base class
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # to make sure we create the tables based on models
# def create_tables():
#     Base.metadata.create_all(bnd=engine)