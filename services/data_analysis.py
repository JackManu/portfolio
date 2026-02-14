"""
Refactored Data Analysis Module
Uses:
- page_views
- video_views
- SQL aggregation
- pandas pivoting
- simplified matplotlib logic
"""

import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D,proj3d
import numpy as np
import io
import base64
import ast
import hashlib
import colorsys
from wordcloud import WordCloud, STOPWORDS
from pathlib import Path
from portfolio_base import Portfolio_Base, PortfolioException

mplstyle.use('fast')
plt.switch_backend('agg')

class DV_base(Portfolio_Base):
    def __init__(self,*args,**kwargs):
        super(DV_base,self).__init__(*args,**kwargs)
        plt.clf()
        plt.figure()
        self.graph_cfg=self.config['graph_cfg']
        self.topic_color_map = {}

        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
            '#bcbd22', '#17becf', '#393b79', '#637939',
            '#8c6d31', '#843c39', '#7b4173', '#3182bd',
            '#31a354', '#756bb1', '#636363', '#e6550d'
        ]
        self.color_idx=0


    def create_graph(self,videos=None):
        img=io.BytesIO()
        graphs={}
        graphs={}
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        graphs['videos']=videos
        return graphs

    def __del__(self):
        plt.close()

class My_DV(DV_base):
    def __init__(self,*args,**kwargs):
        super(My_DV,self).__init__(*args,**kwargs)
        
        self.graphs={}
        self.graphs['errors']=[]
        #self.prune_view_counts()
        self.color_idx=0
        #self.colors=([element for index, element in enumerate(plt.get_cmap('tab10').colors)])
        #self.colors.extend([element for index, element in enumerate(plt.get_cmap('viridis').colors) if index % 50 == 0])
        if kwargs.get('db_list',None):
            self.db_list=kwargs['db_list']
    # -----------------------------------------------------
    # Utility: Create Graph Response
    # -----------------------------------------------------
    def make_graph(self,graph):
        '''
        Function make_graph

        .config has setting 'graph_types'
        key is the graph name, value is the function to run
        '''
        self.logger.debug(f"Trying to run: {str(getattr(self,self.graph_cfg[graph]))}")
       
        output=getattr(self,self.graph_cfg[graph])()

        return output

    def get_color(self, topic=None):
        """
        Returns a consistent color for a topic.
        If topic already assigned, reuse it.
        Otherwise assign next available color.
        """

        if topic in self.topic_color_map:
            return self.topic_color_map[topic]

        # Assign new color
        color = self.colors[self.color_idx]
        self.topic_color_map[topic] = color

        self.color_idx += 1
        if self.color_idx >= len(self.colors):
            self.color_idx = 0

        return color


    # -----------------------------------------------------
    # Wikipedia vs Youtube Hourly Views
    # -----------------------------------------------------
    def wiki_youtube_views(self):

        stmt = """
        SELECT 'Wikipedia' AS type,
               strftime('%Y-%m-%d %H', viewed_at) AS date,
               COUNT(*) AS count
        FROM page_views
        GROUP BY 2

        UNION ALL

        SELECT 'Youtube',
               strftime('%Y-%m-%d %H', viewed_at),
               COUNT(*)
        FROM video_views
        GROUP BY 2
        ORDER BY 2;
        """

        df = pd.read_sql_query(stmt, sqlite3.connect(self.db))

        if df.empty:
            raise PortfolioException("No Data Found", 999)

        pivot = df.pivot_table(
            index='date',
            columns='type',
            values='count',
            fill_value=0
        )

        plt.figure(figsize=(12, 6))
        pivot.plot(marker='.')
        plt.xticks(rotation=45)
        plt.ylabel("Views")
        plt.title("Wikipedia vs Youtube Views")
        plt.grid(True)

        return self.create_graph()

    # -----------------------------------------------------
    # Views By Topic
    # -----------------------------------------------------
    def views_by_topic(self):

        stmt = """
        SELECT w.search_text AS topic,
               strftime('%Y-%m-%d %H', pv.viewed_at) AS date,
               COUNT(*) AS count
        FROM page_views pv
        JOIN Wikipedia w ON pv.page_id = w.id
        GROUP BY 1,2

        UNION ALL

        SELECT w.search_text,
               strftime('%Y-%m-%d %H', vv.viewed_at),
               COUNT(*)
        FROM video_views vv
        JOIN Youtube y ON vv.video_id = y.id
        JOIN Wikipedia w ON y.wiki_id = w.id
        GROUP BY 1,2
        ORDER BY 1,2;
        """

        df = pd.read_sql_query(stmt, sqlite3.connect(self.db))

        if df.empty:
            raise PortfolioException("No Data Found", 999)

        pivot = df.pivot_table(
            index='date',
            columns='topic',
            values='count',
            fill_value=0
        )

        plt.figure(figsize=(14, 6))
        pivot.plot(marker='.')
        plt.xticks(rotation=45)
        plt.ylabel("Views")
        plt.title("Views By Topic")
        plt.grid(True)

        return self.create_graph()

    # -----------------------------------------------------
    # Bubble Chart: Wikipedia vs Youtube Daily Totals
    # -----------------------------------------------------
    def bubble_by_type(self):

        stmt = """
        SELECT 'Wikipedia' AS type,
               strftime('%Y-%m-%d', viewed_at) AS date,
               COUNT(*) AS count
        FROM page_views
        GROUP BY 2

        UNION ALL

        SELECT 'Youtube',
               strftime('%Y-%m-%d', viewed_at),
               COUNT(*)
        FROM video_views
        GROUP BY 2
        ORDER BY 2;
        """

        df = pd.read_sql_query(stmt, sqlite3.connect(self.db))

        if df.empty:
            raise PortfolioException("No Data Found", 999)

        plt.figure(figsize=(12, 6))

        for t in df['type'].unique():
            subset = df[df['type'] == t]
            plt.scatter(
                subset['date'],
                subset['count'],
                s=subset['count'] * 50,
                alpha=0.7,
                label=t
            )

        plt.xticks(rotation=45)
        plt.ylabel("View Count")
        plt.title("Daily Views by Type (Bubble Size = Volume)")
        plt.legend()
        plt.grid(False)

        return self.create_graph()

    def inventory(self):

        db_name = Path(self.db).name

        conn = sqlite3.connect(self.db)

        # --------------------------------------------
        # Main Topic Inventory
        # --------------------------------------------
        topic_stmt = """
            SELECT w.search_text,
                   COUNT(y.id) AS video_count
            FROM Wikipedia w
            JOIN Youtube y ON y.wiki_id = w.id
            GROUP BY w.search_text
            ORDER BY video_count DESC;
        """

        topic_df = pd.read_sql_query(topic_stmt, conn)

        if topic_df.empty:
            conn.close()
            raise PortfolioException("No Inventory Data Found", 999)

        total_videos = topic_df["video_count"].sum()

        # --------------------------------------------
        # Detail Per Wikipedia Entry
        # --------------------------------------------
        detail_data = {}

        for topic in topic_df["search_text"]:

            detail_stmt = """
                SELECT w.title,
                       COUNT(y.id) AS video_count
                FROM Wikipedia w
                JOIN Youtube y ON y.wiki_id = w.id
                WHERE w.search_text = ?
                GROUP BY w.title
                ORDER BY video_count DESC;
            """

            df_detail = pd.read_sql_query(detail_stmt, conn, params=(topic,))
            detail_data[topic] = df_detail

        conn.close()

        # --------------------------------------------
        # Layout Setup
        # --------------------------------------------

        num_topics = len(topic_df)
        fig = plt.figure(figsize=(14, 6 + num_topics * 4))

        grid = gridspec.GridSpec(
            1 + num_topics,   # rows
            1,                # single column
            height_ratios=[3] + [2] * num_topics
        )

        # ============================================
        # TOP PANEL — Main Inventory Bar Chart
        # ============================================

        ax_main = fig.add_subplot(grid[0])

        colors = [self.get_color(topic) for topic in topic_df["search_text"]]

        bars = ax_main.bar(
            topic_df["search_text"],
            topic_df["video_count"],
            color=colors
        )

        for bar in bars:
            height = bar.get_height()
            percent = height / total_videos * 100

            ax_main.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{int(height)} ({percent:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        ax_main.set_ylabel("Total YouTube Videos")
        ax_main.set_title(
            f"YouTube Inventory by Topic\nDatabase: {db_name} — Total Videos: {total_videos}",
            fontsize=14
        )

        ax_main.tick_params(axis="x", rotation=45)

        # ============================================
        # BOTTOM PANELS — Per Topic Detail Charts
        # ============================================

        for i, topic in enumerate(topic_df["search_text"]):

            ax = fig.add_subplot(grid[i + 1])

            df_detail = detail_data[topic]

            if df_detail.empty:
                ax.text(0.5, 0.5, "No Data", ha="center")
                continue

            topic_color = colors[i]

            bars = ax.bar(
                df_detail["title"],
                df_detail["video_count"],
                color=topic_color
            )

            topic_total = df_detail["video_count"].sum()

            for bar in bars:
                height = bar.get_height()
                percent = height / topic_total * 100

                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{int(height)} ({percent:.1f}%)",
                    ha="center",
                    va="bottom",
                    fontsize=8
                )

            ax.set_title(f"{topic} — YouTube per Wikipedia Entry")
            ax.set_ylabel("Video Count")
            ax.set_ylim(0, df_detail["video_count"].max() * 1.25)
            ax.tick_params(axis="x", rotation=45)

        ax_main.set_ylim(0, topic_df["video_count"].max() * 1.25)
        fig.tight_layout()

        return self.create_graph()


    # -----------------------------------------------------
    # YouTube Inventory by Topic
    # -----------------------------------------------------
    def wiki_inventory_by_topic(self):

        stmt = """
            SELECT w.search_text,
                   COUNT(y.id) AS video_count
            FROM Wikipedia w
            JOIN Youtube y ON y.wiki_id = w.id
            GROUP BY w.search_text
            ORDER BY video_count DESC;
        """

        df = pd.read_sql_query(stmt, sqlite3.connect(self.db))

        if df.empty:
            raise PortfolioException("No Data Found", 999)

        plt.figure(figsize=(12, 6))

        # Assign colors per topic
        colors = [self.get_color(topic) for topic in df['search_text']]

        bars=plt.bar(
            df['search_text'],
            df['video_count'],
            color=colors
        )

        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{int(height)}",
                ha='center',
                va='bottom'
            )

        plt.xticks(rotation=45)
        plt.ylabel("Video Count")
        plt.title("YouTube Inventory by Topic")

        plt.tight_layout()

        return self.create_graph()


    # -----------------------------------------------------
    # Word Cloud of Topic Views
    # -----------------------------------------------------
    def views_wordcloud(self):

        stmt = """
        SELECT topic, SUM(count) AS total_views
        FROM (
            SELECT w.search_text AS topic,
                   COUNT(*) AS count
            FROM page_views pv
            JOIN Wikipedia w ON pv.page_id = w.id
            GROUP BY 1

            UNION ALL

            SELECT w.search_text,
                   COUNT(*)
            FROM video_views vv
            JOIN Youtube y ON vv.video_id = y.id
            JOIN Wikipedia w ON y.wiki_id = w.id
            GROUP BY 1
        )
        GROUP BY topic;
        """

        df = pd.read_sql_query(stmt, sqlite3.connect(self.db))

        if df.empty:
            raise PortfolioException("No Data Found", 999)

        tokens = []

        for _, row in df.iterrows():
            tokens.extend([row['topic']] * row['total_views'])

        text_blob = " ".join(tokens)

        wordcloud = WordCloud(
            width=800,
            height=800,
            background_color='white',
            collocations=False,
            stopwords=set(STOPWORDS)
        ).generate(text_blob)

        plt.figure(figsize=(10, 10))
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.title("Topic View WordCloud")

        return self.create_graph()

    def all_youtube_views(self, topic=None):

        plt.clf()

        # ---------------------------------------
        # SQL
        # ---------------------------------------
        stmt = """
            SELECT
                w.search_text AS topic,
                vv.viewed_at,
                y.url,
                y.title,
                y.thumbnail,
                y.id
            FROM video_views vv
            JOIN Youtube y ON vv.video_id = y.id
            JOIN Wikipedia w ON y.wiki_id = w.id
        """

        if topic:
            stmt += " WHERE w.search_text = ? "

        stmt += " ORDER BY vv.viewed_at ASC;"

        conn = sqlite3.connect(self.db)

        if topic:
            df = pd.read_sql_query(stmt, conn, params=(topic,))
        else:
            df = pd.read_sql_query(stmt, conn)

        conn.close()

        if df.empty:

            plt.figure(figsize=(10, 6))

            plt.text(
                0.5,
                0.5,
                "No YouTube Views Recorded Yet",
                ha="center",
                va="center",
                fontsize=16
            )

            plt.xticks([])
            plt.yticks([])
            plt.title("YouTube Viewing Activity")
            plt.tight_layout()

            return self.create_graph(videos={})


        # ---------------------------------------
        # Datetime Handling
        # ---------------------------------------
        df["viewed_at_dt"] = pd.to_datetime(df["viewed_at"])
        df = df.sort_values("viewed_at_dt").reset_index(drop=True)

        # Even horizontal spacing
        df["x_pos"] = df.index

        # Minutes within day
        df["minutes"] = (
            df["viewed_at_dt"].dt.hour * 60 +
            df["viewed_at_dt"].dt.minute
        )

        # ---------------------------------------
        # Setup Figure
        # ---------------------------------------
        fig = plt.figure(figsize=(14, 8))
        ax = fig.add_subplot()

        videos_dict = {}

        # Ensure color mapping exists
        if not hasattr(self, "topic_color_map"):
            self.topic_color_map = {}

        # ---------------------------------------
        # Plot Points
        # ---------------------------------------
        for i, row in df.iterrows():

            topic_name = row["topic"]

            if topic_name not in self.topic_color_map:
                self.topic_color_map[topic_name] = self.get_color(topic_name)

            color = self.topic_color_map[topic_name]

            ax.scatter(
                row["x_pos"],
                row["minutes"],
                color=color,
                marker="o",
                s=60
            )

            # Annotate event index
            ax.annotate(
                i + 1,
                (row["x_pos"], row["minutes"]),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                fontsize=8
            )

            videos_dict[i + 1] = {
                "date": row["viewed_at"],
                "url": row["url"],
                "title": row["title"],
                "thumbnail": ast.literal_eval(row["thumbnail"]),
                "id": row["id"]
            }

        # ---------------------------------------
        # X Axis — Show Date Only When It Changes
        # ---------------------------------------
        date_labels = []
        prev_date = None

        for dt in df["viewed_at_dt"]:
            current_date = dt.date()

            if current_date != prev_date:
                date_labels.append(current_date.strftime("%Y-%m-%d"))
                prev_date = current_date
            else:
                date_labels.append("")

        ax.set_xticks(df["x_pos"])
        ax.set_xticklabels(date_labels, rotation=45)

        ax.set_xlim(df["x_pos"].min() - 0.5,
                    df["x_pos"].max() + 0.5)

        # ---------------------------------------
        # Optional: Vertical Day Separators
        # ---------------------------------------
        prev_date = None
        for i, dt in enumerate(df["viewed_at_dt"]):
            current_date = dt.date()
            if current_date != prev_date and i != 0:
                ax.axvline(i - 0.5,
                           color="gray",
                           linestyle="--",
                           alpha=0.3)
                prev_date = current_date
            else:
                prev_date = current_date

        # ---------------------------------------
        # Y Axis (Hours Clean)
        # ---------------------------------------
        hour_ticks = np.arange(0, 1441, 60)

        hour_labels = [
            f"{h%12 or 12}{'am' if h < 12 else 'pm'}"
            for h in range(24)
        ]
        hour_labels.append("12am")

        ax.set_yticks(hour_ticks)
        ax.set_yticklabels(hour_labels)

        ax.set_ylim(0, 1440)

        # ---------------------------------------
        # Legend
        # ---------------------------------------
        legend_elements = [
            Line2D(
                [0], [0],
                marker='o',
                color='w',
                markerfacecolor=self.topic_color_map[t],
                label=t,
                markersize=8
            )
            for t in self.topic_color_map
        ]

        ax.legend(
            handles=legend_elements,
            loc='center left',
            bbox_to_anchor=(1, 0.5)
        )

        # ---------------------------------------
        # Title & Styling
        # ---------------------------------------
        db_name = Path(self.db).name
        start_date = df["viewed_at_dt"].min().date()
        end_date = df["viewed_at_dt"].max().date()

        plt.title(
            f"YouTube Viewing Activity\n"
            f"{db_name} | {start_date} → {end_date}",
            fontsize=14
        )

        plt.xlabel("Viewing Progression")
        plt.ylabel("Time of Day")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        return self.create_graph(videos=videos_dict)

    # -----------------------------------------------------
    # Viewing Habits Across Multiple Libraries
    # -----------------------------------------------------
    def viewing_habits(self):

        if not hasattr(self, "db_list") or not self.db_list:
            raise PortfolioException("No DB list provided", 999)

        db_totals = {}
        db_topic_breakdown = {}

        for db_path in self.db_list:

            db_name = Path(db_path).name.replace(".db", "")
            conn = sqlite3.connect(db_path)

            # Total YouTube views
            total_stmt = """
                SELECT COUNT(*)
                FROM video_views;
            """

            total = pd.read_sql_query(total_stmt, conn).iloc[0, 0]
            db_totals[db_name] = total

            # Topic breakdown (based on actual views)
            topic_stmt = """
                SELECT w.search_text,
                       COUNT(*) AS view_count
                FROM video_views vv
                JOIN Youtube y ON vv.video_id = y.id
                JOIN Wikipedia w ON y.wiki_id = w.id
                GROUP BY w.search_text
                ORDER BY view_count DESC;
            """

            topic_df = pd.read_sql_query(topic_stmt, conn)
            conn.close()

            db_topic_breakdown[db_name] = topic_df

        # Remove DBs with zero views
        db_totals = {k: v for k, v in db_totals.items() if v > 0}

        if not db_totals:
            raise PortfolioException("No YouTube view data found", 404)

        total_views_all = sum(db_totals.values())

        # Layout
        num_dbs = len(db_totals)
        fig = plt.figure(figsize=(14, 6 + (num_dbs * 5)))
        gs = gridspec.GridSpec(num_dbs + 1, 1, height_ratios=[2] + [3] * num_dbs)

        # =============================
        # Top Pie (DB totals)
        # =============================
        ax0 = fig.add_subplot(gs[0])

        labels = []
        sizes = []

        for db_name, total in db_totals.items():
            percent = (total / total_views_all) * 100
            labels.append(f"{db_name}\n{total} ({percent:.1f}%)")
            sizes.append(total)

        ax0.pie(sizes, labels=labels, startangle=90)
        ax0.set_title(
            f"Total YouTube Views Across Libraries\nTotal Views: {total_views_all}",
            fontsize=14
        )

        # =============================
        # Per-DB Topic Pies
        # =============================
        row_idx = 1

        for db_name, topic_df in db_topic_breakdown.items():

            if db_name not in db_totals:
                continue

            ax = fig.add_subplot(gs[row_idx])
            row_idx += 1

            if topic_df.empty:
                ax.text(0.5, 0.5, "No Topic Data", ha="center", va="center")
                ax.axis("off")
                continue

            db_total = topic_df["view_count"].sum()

            topic_labels = [
                f"{row['search_text']}\n{row['view_count']} ({(row['view_count']/db_total)*100:.1f}%)"
                for _, row in topic_df.iterrows()
            ]

            ax.pie(
                topic_df["view_count"],
                labels=topic_labels,
                startangle=90
            )

            ax.set_title(f"{db_name} — Topic Breakdown\nTotal Views: {db_total}")

        plt.tight_layout()
        return self.create_graph()


    def viewing_surface_3d(self):

        plt.clf()

        # --------------------------------------------
        # Aggregate View Counts by Date and Hour
        # --------------------------------------------
        stmt = """
            SELECT
                strftime('%Y-%m-%d', viewed_at) AS date,
                CAST(strftime('%H', viewed_at) AS INTEGER) AS hour,
                COUNT(*) AS count
            FROM video_views
            GROUP BY 1,2
            ORDER BY 1,2;
        """

        df = pd.read_sql_query(stmt, sqlite3.connect(self.db))

        if df.empty:
            raise PortfolioException("No Viewing Data Found", 404)

        # --------------------------------------------
        # Build Complete Grid (All Hours, All Dates)
        # --------------------------------------------
        all_dates = sorted(df['date'].unique())
        all_hours = list(range(24))

        pivot = df.pivot(index='hour', columns='date', values='count')
        pivot = pivot.reindex(index=all_hours, columns=all_dates, fill_value=0)

        Z = pivot.values

        # Convert dates to numeric index for plotting
        X = np.arange(len(all_dates))
        Y = np.arange(24)

        X, Y = np.meshgrid(X, Y)

        # --------------------------------------------
        # Plot Surface
        # --------------------------------------------
        fig = plt.figure(figsize=(14, 8))
        ax = fig.add_subplot(111, projection='3d')

        surface = ax.plot_surface(
            X, Y, Z,
            cmap='plasma',
            edgecolor='none',
            alpha=0.9
        )

        # --------------------------------------------
        # Axis Labels
        # --------------------------------------------
        ax.set_xlabel("")
        ax.set_ylabel("Hour of Day")
        ax.set_zlabel("View Count")

        hour_ticks = list(range(0, 24, 3))

        hour_labels = [
            "12am","1am","2am","3am","4am","5am",
            "6am","7am","8am","9am","10am","11am",
            "12pm","1pm","2pm","3pm","4pm","5pm",
            "6pm","7pm","8pm","9pm","10pm","11pm"
        ]

        ax.set_yticks(hour_ticks)
        ax.set_yticklabels([hour_labels[h] for h in hour_ticks])

        # Map numeric x positions to actual dates
        ax.set_xticks(range(len(all_dates)))
        ax.set_xticklabels(all_dates, rotation=45, ha='right')

        fig.colorbar(surface, shrink=0.5, aspect=10)

        ax.view_init(elev=30, azim=135)

        plt.title("3D Viewing Habit Surface")

        plt.tight_layout()

        return self.create_graph()

    def inventory_volatility(self):

        db_name = Path(self.db).name

        # --------------------------------------------
        # Pull inventory events
        # --------------------------------------------
        stmt = """
            SELECT topic,
                   event_type,
                   event_timestamp
            FROM inventory_events
            WHERE event_timestamp IS NOT NULL
            ORDER BY event_timestamp ASC;
        """

        conn = sqlite3.connect(self.db)
        df = pd.read_sql_query(stmt, conn)
        conn.close()

        if df.empty:
            raise PortfolioException("No Inventory Events Found", 999)

        # --------------------------------------------
        # Clean & Prepare
        # --------------------------------------------
        df["event_dt"] = pd.to_datetime(df["event_timestamp"], errors="coerce")
        df = df.dropna(subset=["event_dt"])

        if df.empty:
            raise PortfolioException("No Valid Timestamp Data", 998)

        # Normalize to minute resolution
        df["event_dt"] = df["event_dt"].dt.floor("min")

        # Convert event type to delta
        df["delta"] = df["event_type"].map({
            "insert": 1,
            "delete": -1
        })

        df = df.sort_values("event_dt")

        # --------------------------------------------
        # Build per-topic cumulative series
        # --------------------------------------------
        topic_series = {}

        for topic in df["topic"].unique():

            topic_df = df[df["topic"] == topic]

            # Collapse duplicate timestamps safely
            grouped = (
                topic_df
                .groupby("event_dt")["delta"]
                .sum()
                .sort_index()
            )

            topic_series[topic] = grouped.cumsum()

        # Combine safely (outer join)
        inventory_df = pd.concat(topic_series, axis=1)

        # Remove duplicate index labels (critical fix)
        inventory_df = inventory_df[~inventory_df.index.duplicated(keep="last")]

        # Forward fill inventory levels
        inventory_df = inventory_df.sort_index().ffill().fillna(0)

        # Add total inventory line
        inventory_df["Total"] = inventory_df.sum(axis=1)

        # --------------------------------------------
        # Extend to current time (flat leveling)
        # --------------------------------------------
        now = pd.Timestamp.now().floor("min")

        start = inventory_df.index.min()
        end = max(inventory_df.index.max(), now)

        full_range = pd.date_range(start=start, end=end, freq="1min")

        inventory_df = (
            inventory_df
            .reindex(full_range)
            .ffill()
            .fillna(0)
        )

        # --------------------------------------------
        # Plot
        # --------------------------------------------
        plt.figure(figsize=(14, 7))

        topic_columns = [c for c in inventory_df.columns if c != "Total"]

        colors = [self.get_color(topic) for topic in topic_columns]

        plt.stackplot(
            inventory_df.index,
            inventory_df[topic_columns].T,
            labels=topic_columns,
            colors=colors,
            alpha=0.6
        )

        # Total inventory line
        plt.plot(
            inventory_df.index,
            inventory_df["Total"],
            color="black",
            linewidth=2,
            label="Total Inventory"
        )

        # Force full time range visible
        plt.xlim(start, end)

        plt.title(
            f"Inventory Changes (Minute Resolution)\nDatabase: {db_name}",
            fontsize=14
        )

        plt.xlabel("Time")
        plt.ylabel("Inventory Level")

        plt.xticks(rotation=45)
        plt.legend(loc="upper left")

        plt.tight_layout()

        return self.create_graph()

    def viewing_times(self):

        if not hasattr(self, "db_list") or not self.db_list:
            raise PortfolioException("No DB list provided", 999)

        combined_df = pd.DataFrame()

        # -----------------------------------------
        # Collect all video_views from all DBs
        # -----------------------------------------
        for db_path in self.db_list:

            conn = sqlite3.connect(db_path)

            stmt = """
                SELECT viewed_at
                FROM video_views
                WHERE viewed_at IS NOT NULL;
            """

            df = pd.read_sql_query(stmt, conn)
            conn.close()

            if not df.empty:
                combined_df = pd.concat([combined_df, df], ignore_index=True)

        if combined_df.empty:
            raise PortfolioException("No Video View Data Found", 404)

        # -----------------------------------------
        # Convert datetime and extract hour
        # -----------------------------------------
        combined_df["view_dt"] = pd.to_datetime(
            combined_df["viewed_at"],
            errors="coerce"
        )

        combined_df = combined_df.dropna(subset=["view_dt"])

        combined_df["hour"] = combined_df["view_dt"].dt.hour

        # -----------------------------------------
        # Aggregate by hour
        # -----------------------------------------
        hour_counts = combined_df.groupby("hour").size()

        # Ensure all 24 hours exist
        hours = np.arange(24)
        counts = np.array([hour_counts.get(h, 0) for h in hours])

        # Normalize (0–1 scale for better visuals)
        if counts.max() > 0:
            counts = counts / counts.max()

        # -----------------------------------------
        # Create radial plot
        # -----------------------------------------
        angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)

        bars = ax.bar(
            angles,
            counts,
            width=2 * np.pi / 24,
            bottom=0.0
        )

        # Color gradient
        for r, bar in zip(counts, bars):
            bar.set_alpha(0.6 + 0.4 * r)

        # Format clock orientation
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ax.set_xticks(angles)
        ax.set_xticklabels([f"{h}:00" for h in hours])

        ax.set_yticks([])
        ax.set_title(
            "24-Hour YouTube Viewing Rhythm\n(All Databases Combined)",
            va='bottom'
        )

        plt.tight_layout()

        return self.create_graph()

