import sqlite3
import os
import json
import logging
from datetime import datetime, timezone, timedelta


class PortfolioException(Exception):
    """Custom exception class for specific error handling."""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self):
        return f"{self.error_code}: {self.message}"


class Portfolio_Base:
    """
    Base class for portfolio site.

    Handles:
    - DB creation (from config file)
    - Logging
    - Config loading
    - Insert logic
    - SQL execution
    """

    curr_instance_dict = {}

    # -------------------------------------------------
    # Instance Tracking (unchanged)
    # -------------------------------------------------
    @classmethod
    def add_instance_count(cls, class_name=None):
        if class_name:
            cls.curr_instance_dict[class_name] = \
                cls.curr_instance_dict.get(class_name, 0) + 1
        return cls.curr_instance_dict.get(class_name)

    @classmethod
    def del_instance_count(cls, class_name=None):
        if class_name and class_name in cls.curr_instance_dict:
            cls.curr_instance_dict[class_name] -= 1
        return cls.curr_instance_dict.get(class_name)

    # -------------------------------------------------
    # INIT
    # -------------------------------------------------
    def __init__(self, db='./DB/portfolio.db', cfg='./cfg/.config',*args,**kwargs):
        self.db = db.replace(' ', '_')

        self.set_up_logging(log_level='error')
        Portfolio_Base.add_instance_count(self.__class__.__name__)

        # ---------------------
        # Load Config
        # ---------------------
        try:
            with open(cfg, 'r') as cf:
                self.config = json.load(cf)
        except FileNotFoundError as e:
            raise Exception(f"Config file not found: {cfg}") from e
        except Exception as e:
            raise Exception(f"Error loading config: {cfg}") from e

        self.site_db = f'{os.path.dirname(self.db)}/site.db'
        if (not os.path.isfile(self.site_db) or
        os.stat(self.site_db).st_size == 0):
            open(self.site_db, 'w').close()
            self.create_site_db()
        # ---------------------
        # Initialize Database
        # ---------------------
        if not os.path.isfile(self.db):
            self.create_db()

    def __del__(self):
        Portfolio_Base.del_instance_count(self.__class__.__name__)

    def create_site_db(self):
        with sqlite3.connect(self.site_db, timeout=10) as db:
            cursor = db.cursor()

            # Enable WAL mode
            cursor.execute("PRAGMA journal_mode=WAL;")

            for stmt in self.config['SITE_DB_CREATION']:
                cursor.execute(stmt)

            db.commit()
    # -------------------------------------------------
    # Logging Setup
    # -------------------------------------------------
    def set_up_logging(self, log_level="debug"):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        level_dict = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }

        self.logger.setLevel(level_dict[log_level])

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level_dict[log_level])

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    # -------------------------------------------------
    # Create DB Objects from .config
    # -------------------------------------------------
    def create_db(self):
        """
        Reads self.config['DB_CREATION']
        Executes each CREATE TABLE / INDEX statement.
        """

        with sqlite3.connect(self.db,timeout=10) as db:
            cursor = db.cursor()

            try:
                for stmt in self.config['APP_DB_CREATION']:
                    cursor.execute(stmt)
                db.commit()
                cursor.execute("PRAGMA journal_mode=WAL;")
                db.commit()
            except sqlite3.Error as e:
                raise Exception(f"Error creating DB objects: {e}") from e

    # -------------------------------------------------
    # Time Utility
    # -------------------------------------------------
    def get_curr_date(self, format_string=None, round_min=None):
        """
        Returns current datetime in PST.
        round_min kept for backward compatibility (not used).
        """

        timezone_offset = -8.0  # Pacific Standard Time
        tzinfo = timezone(timedelta(hours=timezone_offset))
        now = datetime.now(tzinfo)

        if format_string:
            return now.strftime(format_string)

        return now.strftime("%Y-%m-%d %H:%M:%S")


    # -------------------------------------------------
    # INSERTS
    # -------------------------------------------------
    def db_insert(self, **kwargs):
        """
        Generic insert handler.
        """

        with sqlite3.connect(self.db) as db:
            cursor = db.cursor()
            now = self.get_curr_date()

            try:

                # ------------------------
                # Wikipedia
                # ------------------------
                if kwargs['table_name'] == 'Wikipedia':
                    cursor.execute("""
                        INSERT OR REPLACE INTO Wikipedia
                        (id, creation_date, search_text, title, url, description, thumbnail)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        kwargs['my_id'],
                        now,
                        kwargs['search_text'],
                        kwargs['title'],
                        kwargs['url'],
                        kwargs['description'],
                        str(kwargs['thumbnail'])
                    ))

                # ------------------------
                # Youtube
                # ------------------------
                elif kwargs['table_name'] == 'Youtube':
                    cursor.execute("""
                        INSERT OR REPLACE INTO Youtube
                        (id, creation_date, wiki_id, video_id, title, url, description, thumbnail)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        kwargs['my_id'],
                        now,
                        kwargs['wiki_id'],
                        kwargs['video_id'],
                        kwargs['title'],
                        kwargs['url'],
                        kwargs['description'],
                        str(kwargs['thumbnail'])
                    ))

                # ------------------------
                # Page View (NEW)
                # ------------------------
                elif kwargs['table_name'] == 'page_views':
                    cursor.execute("""
                        INSERT INTO page_views (page_id, viewed_at)
                        VALUES (?, ?)
                    """, (
                        kwargs['page_id'],
                        now
                    ))

                # ------------------------
                # Video View (NEW)
                # ------------------------
                elif kwargs['table_name'] == 'video_views':
                    cursor.execute("""
                        INSERT INTO video_views (video_id, viewed_at)
                        VALUES (?, ?)
                    """, (
                        kwargs['video_id'],
                        now
                    ))
                elif kwargs['table_name'] == 'site_traffic_init':
                    cursor.execute("""
                        INSERT INTO site_traffic_init
                        (creation_date, route, display_date)
                        VALUES (?, ?, ?)
                        """, (
                        now,
                        kwargs['route'],
                        kwargs['display_date']
                    ))
                elif kwargs['table_name'] == 'comments':
                    cursor.execute("""
                        INSERT INTO comments
                        (creation_date, user_email, comment)
                        VALUES (?, ?, ?)
                        """, (
                        now,
                        str(kwargs.get('user_email', '')),
                        str(kwargs.get('comment', ''))
                    ))
                # ------------------------
                # Errors
                # ------------------------
                elif kwargs['table_name'] == 'errors':
                    cursor.execute("""
                        INSERT INTO errors
                        (creation_date, type, module_name, error_text)
                        VALUES (?, ?, ?, ?)
                    """, (
                        now,
                        str(kwargs['type']),
                        str(kwargs['module_name']),
                        str(kwargs['error_text'])
                    ))

                db.commit()

            except sqlite3.Error as e:
                raise Exception(f"db_insert failed: {e}") from e

    def exec_statement(self, stmt, params=None):
        #self.logger.debug(f"Exec statement: {stmt}  params: {params}")
        with sqlite3.connect(self.db) as db:
            cursor = db.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
        try:
            if params is None:
                cursor.execute(stmt)

            else:
                # Normalize single parameter
                if not isinstance(params, (list, tuple)):
                    params = (params,)

                cursor.execute(stmt, params)
            db.commit()
            return cursor.fetchall()

        except sqlite3.OperationalError as e:
            '''
            self.db_insert(
                table_name='errors',
                type='SQL',
                module_name=self.__class__.__name__,
                error_text=f'statement: {stmt} exception: {e}'
            )
            '''
            self.logger.error(f"SQL execution failed: {e}")
            raise Exception(f"SQL execution failed: {e}") from e
        finally:
            cursor.close()
            db.close()


