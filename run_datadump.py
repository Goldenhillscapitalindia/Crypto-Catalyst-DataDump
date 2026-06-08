"""
=============================================================================
  Crypto Catalyst DataDump  —  Daily Main Runner
=============================================================================
  Run this single file every day to populate all ETL-owned tables.

  TABLE OWNERSHIP MAP
  ───────────────────
  [SQL Server → PG  | incremental append]
      crypto_average_true_range
      crypto_daily_beta
      crypto_prices_main
      crypto_volume_20_data
      crypto_volume_data

  [SQL Server → PG  | truncate + full insert]
      crypto_master
      crypto_technical_indicators_daily
      crypto_performance
      crypto_target_prices

  [SQL Server → PG  | merge EMA + MA + MACD]
      crypto_ma_ema_macd

  [SQL Server pyodbc → PG | truncate + full insert]
      us_market_index

  [EOD API → PG]
      crypto_all_tickers          (daily truncate+insert)
      crypto_live_data            (daily truncate+insert)
      crypto_historical_data      (daily truncate+insert)
      crypto_all_ticker_historical_data  (50-MA processed, daily truncate+insert)

  [Computed inside PG → PG | truncate + recompute]
      crypto_super_screener

  NOTE: The following tables are Django-app managed and are NOT touched here:
      auth_*, django_*, portfolio, report, watchlist_data,
      crypto_daily_ico_data, crypto_daily_news,
      crypto_index_dataset, crypto_index_wizard
=============================================================================
"""

# ── Imports ──────────────────────────────────────────────────────────────────
import os
import sys
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import numpy as np
import pandas as pd
import pyodbc
import requests
from sqlalchemy import create_engine, text

# ── Configuration ─────────────────────────────────────────────────────────────

# PostgreSQL  (destination)
PG_DB       = 'CRYPTO DEVELOPMENT'
PG_USER     = 'postgres'
PG_PASSWORD = 'GhcHyd_2025$'
PG_HOST     = '192.168.1.68'
PG_PORT     = 5432

# SQL Server  (source)
SQL_DB      = '72PI'
SQL_USER    = '72pi'
SQL_PASSWORD= '72Pi_2023$'
SQL_HOST    = '192.168.1.5'
SQL_PORT    = 1433
SQL_DRIVER  = 'ODBC Driver 13 for SQL Server'

# EOD Historical Data API
EOD_TOKEN   = '612f4f7f3906a3.86934021'

# Email notifications
MAIL_FROM   = 'ghcit@goldenhillsindia.com'
MAIL_PASS   = 'Afsadmin2023$$$$$$$'
MAIL_TO     = [
    'vasanthi.g@goldenhillsindia.com',
    'charan.d@goldenhillsindia.com',
    'ranjith.a@goldenhillsindia.com',
]

# Paths
BASE_DIR        = r'I:\72PI Daily Data\Crypto Catalyst'
OUT_TICKERS     = os.path.join(BASE_DIR, r'output_file\All_tickers_data')
OUT_HIST        = os.path.join(BASE_DIR, r'output_file\All_tickers_historical_data')

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(BASE_DIR, 'datadump.log'), encoding='utf-8'
        ),
    ],
)
log = logging.getLogger('datadump')


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def pg_engine():
    url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url, pool_pre_ping=True)


def sql_engine():
    url = (
        f"mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}"
        f"@{SQL_HOST}:{SQL_PORT}/{SQL_DB}?driver={SQL_DRIVER}"
    )
    return create_engine(url, pool_pre_ping=True)


def sql_pyodbc():
    """Direct pyodbc connection (used where SQLAlchemy MSSQL is unavailable)."""
    cs = (
        f"DRIVER={{{SQL_DRIVER}}};SERVER={SQL_HOST},{SQL_PORT};"
        f"DATABASE={SQL_DB};UID={SQL_USER};PWD={SQL_PASSWORD}"
    )
    return pyodbc.connect(cs)


def truncate_table(engine, table: str):
    """TRUNCATE a PostgreSQL table inside its own transaction."""
    with engine.begin() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{table}"'))


def df_to_pg(df: pd.DataFrame, table: str, engine, chunk: int = 500):
    """Append a DataFrame to a PostgreSQL table."""
    df.to_sql(
        name=table, con=engine,
        if_exists='append', index=False,
        method='multi', chunksize=chunk,
    )


def stamp(df: pd.DataFrame) -> pd.DataFrame:
    """Add created_at / updated_at timestamp columns."""
    today = datetime.now().date()
    df = df.copy()
    df['created_at'] = today
    df['updated_at']  = today
    return df


def latest_date_in_pg(engine, table: str, date_col: str = '"Date"'):
    """Return the latest date already loaded in a PG table (or 1900-01-01)."""
    row = pd.read_sql(f'SELECT MAX({date_col}) FROM "{table}"', engine)
    val = row.iloc[0, 0]
    return pd.to_datetime('1900-01-01') if val is None else pd.to_datetime(val)


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 1  –  SQL Server → PostgreSQL  (incremental + truncate)
# ═══════════════════════════════════════════════════════════════════════════════

def step_sql_migration(pg, sql):
    log.info("── STEP 1 : SQL Server → PostgreSQL migration ──")

    DELTA = 0   # extra days to overlap / re-insert

    # ── 1A  Incremental-append tables ────────────────────────────────────────
    APPEND_TABLES = [
        'crypto_average_true_range',
        'crypto_daily_beta',
        'crypto_prices_main',
        'crypto_volume_20_data',
        'crypto_volume_data',
    ]

    for tbl in APPEND_TABLES:
        try:
            latest = latest_date_in_pg(pg, tbl)

            exists = pd.read_sql(
                f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_NAME = '{tbl}'", sql
            )
            if exists.empty:
                log.warning(f"   {tbl} — not found in SQL Server, skipped")
                continue

            new_data = pd.read_sql(
                f"SELECT * FROM {tbl} WHERE Date > '{latest}'", sql
            )
            if new_data.empty:
                log.info(f"   {tbl} — already up-to-date")
                continue

            new_data = new_data.drop(columns=['id'], errors='ignore')

            # Delete overlap window from PG then re-insert
            cutoff = latest - timedelta(days=DELTA)
            with pg.begin() as conn:
                conn.execute(text(
                    f'DELETE FROM "{tbl}" WHERE "Date" > \'{cutoff}\''
                ))

            # Assign sequential IDs
            max_id_row = pd.read_sql(f'SELECT MAX(id) FROM "{tbl}"', pg)
            max_id = int(max_id_row.iloc[0, 0] or 0)
            new_data.insert(0, 'id', range(max_id + 1, max_id + len(new_data) + 1))
            new_data.columns = new_data.columns.str.replace(' ', '_')
            df_to_pg(new_data, tbl, pg)
            log.info(f"   {tbl} — +{len(new_data)} rows appended")

        except Exception as exc:
            log.error(f"   {tbl} — ERROR: {exc}")

    # ── 1B  Truncate + full-insert tables ─────────────────────────────────────
    TRUNCATE_TABLES = [
        'crypto_master',
        'crypto_technical_indicators_daily',
        'crypto_performance',
        'crypto_target_prices',
    ]

    for tbl in TRUNCATE_TABLES:
        try:
            data = pd.read_sql(f"SELECT * FROM {tbl}", sql)
            truncate_table(pg, tbl)
            df_to_pg(data, tbl, pg)
            log.info(f"   {tbl} — {len(data)} rows (truncated + inserted)")
        except Exception as exc:
            log.error(f"   {tbl} — ERROR: {exc}")

    # ── 1C  Merge  EMA + MA + MACD  →  crypto_ma_ema_macd ───────────────────
    try:
        df_ema = pd.read_sql(
            'SELECT * FROM Crypto_Exponential_Moving_Average '
            'ORDER BY FS_Ticker, Date', sql
        )[['Company','FS_Ticker','Date','Price',
           'EMA9','EMA12','EMA','EMA26','EMA50','EMA200']]

        df_ma = pd.read_sql(
            'SELECT * FROM Crypto_Moving_Average '
            'ORDER BY FS_Ticker, Date', sql
        )[['Date','FS_Ticker','9MA','20MA','26MA','50MA','100MA','200MA']]

        df_macd = pd.read_sql(
            'SELECT * FROM Crypto_Moving_Average_Convergence_Divergence '
            'ORDER BY FS_Ticker, Date', sql
        )[['Date','FS_Ticker','MACD Line','Signal Line','MACD Histogram']]

        merged = (
            df_ema
            .merge(df_ma,   on=['FS_Ticker','Date'])
            .merge(df_macd, on=['FS_Ticker','Date'])
        )

        latest = latest_date_in_pg(pg, 'crypto_ma_ema_macd')
        cutoff  = latest - timedelta(days=DELTA)
        new_rows = merged[merged['Date'] > cutoff].copy()
        new_rows.columns = new_rows.columns.str.replace(' ', '_')
        new_rows['created_at'] = datetime.now().date()
        new_rows['updated_at']  = datetime.now().date()
        df_to_pg(new_rows, 'crypto_ma_ema_macd', pg)
        log.info(f"   crypto_ma_ema_macd — +{len(new_rows)} rows appended")

    except Exception as exc:
        log.error(f"   crypto_ma_ema_macd — ERROR: {exc}")

    log.info("── STEP 1 done ──\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 2  –  US Market Index  (SQL Server pyodbc → PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════════

def step_us_market_index(pg):
    log.info("── STEP 2 : US Market Index ──")
    try:
        with sql_pyodbc() as conn:
            df = pd.read_sql('SELECT * FROM US_Market_Index', conn)

        df['created_at'] = datetime.now()
        df['updated_at']  = datetime.now()
        truncate_table(pg, 'us_market_index')
        df_to_pg(df, 'us_market_index', pg, chunk=1000)
        log.info(f"   us_market_index — {len(df)} rows (truncated + inserted)")

    except Exception as exc:
        log.error(f"   us_market_index — ERROR: {exc}")

    log.info("── STEP 2 done ──\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 3  –  EOD API → PostgreSQL  (live, historical, 50-MA summary)
# ═══════════════════════════════════════════════════════════════════════════════

def step_live_historical(pg):
    log.info("── STEP 3 : EOD API  →  PostgreSQL ──")

    today     = datetime.today().date()
    yesterday = today - timedelta(days=1)

    # ── 3A  All tickers ───────────────────────────────────────────────────────
    try:
        log.info("   Downloading all crypto tickers …")
        resp = requests.get(
            'https://eodhistoricaldata.com/api/exchange-symbol-list/CC'
            f'?api_token={EOD_TOKEN}&fmt=json', timeout=60
        )
        resp.raise_for_status()
        tickers_df = pd.DataFrame(resp.json())
        tickers_df['Date'] = today.strftime('%Y-%m-%d')
        tickers_df = stamp(tickers_df)

        truncate_table(pg, 'crypto_all_tickers')
        df_to_pg(tickers_df, 'crypto_all_tickers', pg)
        tickers_df.to_excel(
            os.path.join(OUT_TICKERS, 'crypto_all_tickers.xlsx'), index=False
        )
        log.info(f"   crypto_all_tickers — {len(tickers_df)} tickers saved")

        tickers_list = (tickers_df['Code'] + '.CC').tolist()

    except Exception as exc:
        log.error(f"   crypto_all_tickers — ERROR: {exc}")
        log.warning("   Cannot continue Step 3 without tickers, aborting step")
        return

    # ── 3B  Live prices ───────────────────────────────────────────────────────
    live_df = pd.DataFrame()
    try:
        max_row = pd.read_sql(
            'SELECT MAX("Downloaded_Date") FROM crypto_live_data', pg
        )
        max_date = max_row.iloc[0, 0]
        max_date = max_date.date() if max_date is not None else None

        if max_date == today:
            log.info("   crypto_live_data — already downloaded today, reading from DB")
            live_df = pd.read_sql('SELECT * FROM crypto_live_data', pg)
            live_df = live_df.drop(
                columns=['id','created_at','updated_at'], errors='ignore'
            )
        else:
            log.info(f"   Downloading live prices for {len(tickers_list)} tickers …")
            CHUNK = 15
            raw = []
            for i in range(0, len(tickers_list), CHUNK):
                chunk = tickers_list[i:i + CHUNK]
                url = (
                    f'https://eodhd.com/api/real-time/{chunk[0]}'
                    f'?s={",".join(chunk[1:])}'
                    f'&api_token={EOD_TOKEN}&fmt=json'
                )
                try:
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        raw.extend(data if isinstance(data, list) else [data])
                except Exception:
                    pass   # individual chunk failure — continue

            if raw:
                live_df = pd.DataFrame(raw)
                live_df = live_df.rename(columns={
                    'code':'Code','timestamp':'Timestamp','gmtoffset':'GmtOffset',
                    'open':'Open','high':'High','low':'Low','close':'Close',
                    'volume':'Volume','previousClose':'PreviousClose',
                    'change':'Change','change_p':'ChangeP',
                })
                live_df['Timestamp'] = pd.to_numeric(
                    live_df['Timestamp'].replace('NA', np.nan), errors='coerce'
                )
                live_df = live_df.dropna(subset=['Timestamp'])
                live_df['Date'] = (
                    pd.to_datetime(live_df['Timestamp'], unit='s', utc=True)
                      .dt.tz_convert('Asia/Kolkata')
                      .dt.tz_localize(None)
                )
                live_df['Downloaded_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                live_df['ChangeP'] = pd.to_numeric(
                    live_df.get('ChangeP', pd.Series(dtype='float'))
                          .replace('NA', 0), errors='coerce'
                ).fillna(0)
                for col in ['Open','High','Low','Close','Volume','PreviousClose','Change']:
                    if col in live_df.columns:
                        live_df[col] = pd.to_numeric(
                            live_df[col].replace('NA', np.nan), errors='coerce'
                        )
                live_df = live_df.dropna(subset=['Close'])
                live_df = live_df.drop(columns=['Timestamp'], errors='ignore')
                live_df = stamp(live_df)

                live_df.to_excel(
                    os.path.join(OUT_TICKERS, 'live_crypto_data.xlsx'), index=False
                )
                truncate_table(pg, 'crypto_live_data')
                df_to_pg(live_df, 'crypto_live_data', pg)
                log.info(f"   crypto_live_data — {len(live_df)} rows saved")
            else:
                log.warning("   Live data fetch returned no results")

    except Exception as exc:
        log.error(f"   crypto_live_data — ERROR: {exc}")

    # ── 3C  Historical prices ─────────────────────────────────────────────────
    hist_df = pd.DataFrame()
    try:
        max_row = pd.read_sql(
            'SELECT MAX("Downloaded_Date") FROM crypto_historical_data', pg
        )
        max_hist = max_row.iloc[0, 0]
        max_hist = max_hist.date() if max_hist is not None else None

        if max_hist == yesterday:
            log.info("   crypto_historical_data — already downloaded, reading from DB")
            hist_df = pd.read_sql('SELECT * FROM crypto_historical_data', pg)
            hist_df = hist_df.drop(
                columns=['id','created_at','updated_at'], errors='ignore'
            )
        else:
            log.info(f"   Downloading historical prices for {len(tickers_list)} tickers …")
            parts, failed = [], []
            for i, ticker in enumerate(tickers_list):
                try:
                    r = requests.get(
                        f'https://eodhistoricaldata.com/api/eod/{ticker}'
                        f'?api_token={EOD_TOKEN}&fmt=json', timeout=30
                    )
                    r.raise_for_status()
                    df = pd.DataFrame(r.json())
                    if df.empty:
                        continue
                    df['Ticker'] = ticker.replace('.CC', '')
                    df = df[df['date'] >= '2017-01-01']
                    df['date'] = pd.to_datetime(df['date'])
                    df = df[df['date'].dt.date != today]
                    parts.append(df)
                except Exception:
                    failed.append(ticker)

                if (i + 1) % 200 == 0:
                    log.info(f"   … {i + 1}/{len(tickers_list)} done, "
                             f"{len(failed)} failed so far")

            if parts:
                hist_df = pd.concat(parts, ignore_index=True)
                hist_df['Downloaded_Date'] = yesterday.strftime('%Y-%m-%d')
                hist_df = hist_df.rename(columns={
                    'date':'Date','open':'Open','high':'High','low':'Low',
                    'close':'Close','adjusted_close':'Adjusted_Close',
                    'volume':'Volume',
                })
                hist_df = hist_df[[
                    'Date','Open','High','Low','Close',
                    'Adjusted_Close','Volume','Ticker','Downloaded_Date'
                ]]
                hist_df = stamp(hist_df)

                truncate_table(pg, 'crypto_historical_data')
                df_to_pg(hist_df, 'crypto_historical_data', pg, chunk=1000)
                log.info(
                    f"   crypto_historical_data — {len(hist_df)} rows saved "
                    f"({len(failed)} tickers failed)"
                )
            else:
                log.warning("   No historical data downloaded")

    except Exception as exc:
        log.error(f"   crypto_historical_data — ERROR: {exc}")

    # ── 3D  50-MA processing  →  crypto_all_ticker_historical_data + Excel ───
    try:
        if hist_df.empty:
            # Fall back to DB
            hist_df = pd.read_sql('SELECT * FROM crypto_historical_data', pg)
            hist_df = hist_df.drop(
                columns=['id','created_at','updated_at'], errors='ignore'
            )

        # Normalise dates
        hist_df['Date'] = pd.to_datetime(
            hist_df['Date'], utc=True, errors='coerce'
        ).dt.date
        hist_df = hist_df[hist_df['Date'] <= yesterday]
        hist_df['Date'] = pd.to_datetime(hist_df['Date'])

        # Combine with today's live close
        if not live_df.empty and 'Code' in live_df.columns:
            live_part = live_df[['Code','Downloaded_Date','Close','Volume']].copy()
            live_part = live_part.rename(columns={
                'Code':'Ticker','Downloaded_Date':'Date','Close':'Price'
            })
        else:
            live_part = pd.DataFrame(columns=['Ticker','Date','Price','Volume'])

        hist_part = hist_df[['Ticker','Date','Adjusted_Close','Volume']].rename(
            columns={'Adjusted_Close':'Price'}
        )
        final = pd.concat([hist_part, live_part], ignore_index=True)
        final['Date'] = pd.to_datetime(
            final['Date'], utc=True, errors='coerce'
        ).dt.date

        cutoff = today - timedelta(days=100)
        final  = final[final['Date'] >= cutoff].sort_values(['Ticker','Date'])
        final['Date'] = pd.to_datetime(final['Date'])

        # 50-day moving average & crossover signals
        final['50_day_MA'] = (
            final.groupby('Ticker')['Price']
                 .transform(lambda x: x.rolling(50, min_periods=1).mean())
        )
        final['price_ma_diff']    = final['Price'] - final['50_day_MA']
        final['price_gt_ma']      = (final['Price'] > final['50_day_MA']).astype(int)
        final['prev_price_gt_ma'] = (
            final.groupby('Ticker')['price_gt_ma'].shift(1)
        )
        final['Volume_diff'] = final.groupby('Ticker')['Volume'].diff()
        final = final.reset_index(drop=True)

        latest_rows  = final.groupby('Ticker').tail(1)
        top_volume   = (
            latest_rows.sort_values('Volume_diff', ascending=False).head(10)
        )
        top_ma_cross = (
            latest_rows[
                (latest_rows['price_gt_ma'] == 1) &
                (latest_rows['prev_price_gt_ma'] == 0)
            ]
            .sort_values('price_ma_diff', ascending=False)
            .head(10)
        )

        # Save Excel summary
        out_xlsx = os.path.join(
            OUT_HIST, f'Volume_50MA_Daily_Summary_{today}.xlsx'
        )
        with pd.ExcelWriter(out_xlsx, engine='xlsxwriter') as w:
            final.to_excel(      w, sheet_name='Historical_data',      index=False)
            latest_rows.to_excel(w, sheet_name='Today_Summary',        index=False)
            top_volume.to_excel( w, sheet_name='Volume_Top_10',        index=False)
            top_ma_cross.to_excel(w, sheet_name='50MA_Crossed_Top_10', index=False)
        log.info(f"   Excel summary → {os.path.basename(out_xlsx)}")

        # Save to crypto_all_ticker_historical_data
        save_df = stamp(final.copy())
        truncate_table(pg, 'crypto_all_ticker_historical_data')
        df_to_pg(save_df, 'crypto_all_ticker_historical_data', pg, chunk=1000)
        log.info(
            f"   crypto_all_ticker_historical_data — {len(save_df)} rows saved"
        )

    except Exception as exc:
        log.error(f"   50-MA / crypto_all_ticker_historical_data — ERROR: {exc}")

    log.info("── STEP 3 done ──\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 4  –  Crypto Super Screener  (PG merge → crypto_super_screener)
# ═══════════════════════════════════════════════════════════════════════════════

def step_super_screener(pg):
    log.info("── STEP 4 : Crypto Super Screener ──")
    try:

        def _latest_per_ticker(df: pd.DataFrame) -> pd.DataFrame:
            """Keep only the most-recent row per FS_Ticker."""
            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return (
                df.sort_values('Date')
                  .groupby('FS_Ticker', as_index=False)
                  .tail(1)
                  .drop(columns=['Date'])
            )

        # ── Read source tables ────────────────────────────────────────────────
        tech_df = pd.read_sql(
            'SELECT "Date","FS_Ticker","Symbol","Company","Price","Return","Net_Change",'
            '"MA9_MA20_Value","MA20_MA50_Value","MA50_MA200_Value","RSI_Value","CCI_Value",'
            '"Williams_Value","StochRSI_Value","Stochastics_Value","MACD_Value","ATR_Value",'
            '"ADX_Value","Super_Trend_Value","MFI_Value","PVO_Value","CMF_Value",'
            '"Moving_Average_Rating","Momentum_Rating","Trend_Rating","Volume_Rating",'
            '"Final_Rating" FROM crypto_technical_indicators_daily',
            pg,
        )
        # Normalise timezone
        if pd.api.types.is_datetime64tz_dtype(tech_df['Date']):
            tech_df['Date'] = tech_df['Date'].dt.tz_convert('Asia/Kolkata')
        else:
            tech_df['Date'] = pd.to_datetime(tech_df['Date'])

        master_df = pd.read_sql(
            'SELECT "FS_Ticker","Security_Code","MarketCapDominance",'
            '"MarketCapitalization","MaxSupply","TotalSupply","Beta_1Y"'
            ' FROM crypto_master',
            pg,
        )
        ma_df = _latest_per_ticker(pd.read_sql(
            'SELECT "FS_Ticker","Date","EMA9","EMA12","EMA","EMA26","EMA50","EMA200",'
            '"9MA","20MA","26MA","50MA","100MA","200MA"'
            ' FROM crypto_ma_ema_macd',
            pg,
        ))
        atr_df = _latest_per_ticker(pd.read_sql(
            'SELECT "FS_Ticker","Date","Volume" FROM crypto_average_true_range',
            pg,
        ))
        target_df = pd.read_sql(
            'SELECT "FS_Ticker","52_Week_High","52_Week_Low","1M_High","1M_Low"'
            ' FROM crypto_target_prices',
            pg,
        )
        perf_df = pd.read_sql(
            'SELECT "FS_Ticker","2017toDate","YTD","MTD","1Y"'
            ' FROM crypto_performance',
            pg,
        )

        # ── Merge all on FS_Ticker ────────────────────────────────────────────
        merged = tech_df.copy()
        for df in [master_df, ma_df, atr_df, target_df, perf_df]:
            merged = merged.merge(df, on='FS_Ticker', how='left')

        # Strip timezone from Date
        if pd.api.types.is_datetime64tz_dtype(merged['Date']):
            merged['Date'] = merged['Date'].dt.tz_localize(None)

        merged.insert(0, 'id', range(1, len(merged) + 1))
        merged['created_at'] = datetime.now().date()
        merged['updated_at']  = datetime.now().date()

        truncate_table(pg, 'crypto_super_screener')
        df_to_pg(merged, 'crypto_super_screener', pg)
        log.info(f"   crypto_super_screener — {len(merged)} rows saved")

    except Exception as exc:
        log.error(f"   crypto_super_screener — ERROR: {exc}")

    log.info("── STEP 4 done ──\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  Email notification
# ═══════════════════════════════════════════════════════════════════════════════

def send_email(subject: str, html_body: str):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From']    = MAIL_FROM
        msg['To']      = ', '.join(MAIL_TO)
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(MAIL_FROM, MAIL_PASS)
            s.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
        log.info("Email sent successfully")
    except Exception as exc:
        log.warning(f"Email failed: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    start = datetime.now()
    log.info("=" * 65)
    log.info(f"  Crypto Catalyst DataDump  —  {start:%Y-%m-%d %H:%M:%S}")
    log.info("=" * 65 + "\n")

    step_errors: list[str] = []

    # Build engines once; pass them through
    pg  = pg_engine()
    sql = sql_engine()

    steps = [
        ("SQL Server → PostgreSQL migration",  lambda: step_sql_migration(pg, sql)),
        ("US Market Index",                    lambda: step_us_market_index(pg)),
        ("EOD API  →  PostgreSQL",             lambda: step_live_historical(pg)),
        ("Crypto Super Screener",              lambda: step_super_screener(pg)),
    ]

    for name, fn in steps:
        try:
            fn()
        except Exception as exc:
            msg = f"{name}: {exc}"
            log.error(f"FATAL – {msg}")
            step_errors.append(msg)

    # Close DB connections
    pg.dispose()
    sql.dispose()

    elapsed = datetime.now() - start
    mins, secs = divmod(elapsed.seconds, 60)

    log.info("=" * 65)
    if step_errors:
        log.warning(f"  Completed with {len(step_errors)} error(s) in {mins}m {secs}s")
        for e in step_errors:
            log.warning(f"    • {e}")
    else:
        log.info(f"  All steps completed successfully in {mins}m {secs}s")
    log.info("=" * 65)

    # ── Tables updated summary ────────────────────────────────────────────────
    table_list = """
    <li>crypto_average_true_range</li>
    <li>crypto_daily_beta</li>
    <li>crypto_prices_main</li>
    <li>crypto_volume_20_data</li>
    <li>crypto_volume_data</li>
    <li>crypto_master</li>
    <li>crypto_technical_indicators_daily</li>
    <li>crypto_performance</li>
    <li>crypto_target_prices</li>
    <li>crypto_ma_ema_macd</li>
    <li>us_market_index</li>
    <li>crypto_all_tickers</li>
    <li>crypto_live_data</li>
    <li>crypto_historical_data</li>
    <li>crypto_all_ticker_historical_data</li>
    <li>crypto_super_screener</li>
    """

    if step_errors:
        subject = "⚠ Crypto Catalyst DataDump — Completed with Errors"
        body = (
            f"<p>DataDump finished in <b>{mins}m {secs}s</b> with "
            f"<b>{len(step_errors)}</b> error(s):</p>"
            f"<ul>{''.join(f'<li>{e}</li>' for e in step_errors)}</ul>"
            f"<p>Tables attempted:</p><ul>{table_list}</ul>"
        )
    else:
        subject = "✅ Crypto Catalyst DataDump — Completed Successfully"
        body = (
            f"<p>All steps completed in <b>{mins}m {secs}s</b>.</p>"
            f"<p>Tables updated:</p><ul>{table_list}</ul>"
        )

    send_email(subject, body)


if __name__ == '__main__':
    os.chdir(BASE_DIR)
    os.makedirs(OUT_TICKERS, exist_ok=True)
    os.makedirs(OUT_HIST,    exist_ok=True)
    main()
