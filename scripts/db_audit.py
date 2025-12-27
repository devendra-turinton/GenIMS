#!/usr/bin/env python3
"""
Database Audit Script
Reports, for each GenIMS database:
- Total number of user tables
- Total number of columns (sum across tables)
- Per-table column count and exact row count (configurable to use estimates)

Uses connection info and database names from scripts/full_setup.py and .env.
Outputs a Markdown report to Database_Audit_Report.md and prints a concise summary.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Resolve repo root and load .env
REPO_ROOT = Path(__file__).parent.parent
ENV_PATH = REPO_ROOT / '.env'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Import database config from full_setup without executing any setup
sys.path.insert(0, str((REPO_ROOT / 'scripts').resolve()))
from full_setup import DATABASES, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD  # type: ignore


def connect(dbname: str):
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=dbname,
    )


def list_user_tables(conn):
    """Return list of (schema, table) for base tables excluding system schemas."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog','information_schema')
            ORDER BY table_schema, table_name
            """
        )
        return cur.fetchall()


def count_columns(conn, schema: str, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        return cur.fetchone()[0]


def count_rows_exact(conn, schema: str, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SET LOCAL statement_timeout = '10min';"))
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}.{};").format(
            sql.Identifier(schema), sql.Identifier(table)
        ))
        return cur.fetchone()[0]


def count_rows_estimate(conn, schema: str, table: str) -> int:
    """Fast estimate from pg_class.reltuples (can be off, but quick)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.reltuples::BIGINT AS estimate
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = %s AND c.relkind = 'r'
            """,
            (schema, table),
        )
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


def audit_database(dbname: str, row_method: str):
    result = {
        'database': dbname,
        'tables_total': 0,
        'columns_total': 0,
        'tables': [],  # list of dicts: schema, table, columns, rows
    }
    conn = connect(dbname)
    try:
        tables = list_user_tables(conn)
        result['tables_total'] = len(tables)

        for schema, table in tables:
            cols = count_columns(conn, schema, table)
            if row_method == 'exact':
                rows = count_rows_exact(conn, schema, table)
            else:
                rows = count_rows_estimate(conn, schema, table)

            result['columns_total'] += cols
            result['tables'].append({
                'schema': schema,
                'table': table,
                'columns': cols,
                'rows': rows,
            })
    finally:
        conn.close()

    return result


def write_markdown_report(results, out_path: Path, row_method: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = []
    lines.append(f"# GenIMS PostgreSQL Database Audit Report")
    lines.append("")
    lines.append(f"Generated: {ts}")
    lines.append(f"Row count method: {row_method}")
    lines.append("")

    for res in results:
        lines.append(f"## {res['database']}")
        lines.append(f"- Total Tables: {res['tables_total']}")
        lines.append(f"- Total Columns: {res['columns_total']}")
        total_rows = sum(t['rows'] for t in res['tables'])
        lines.append(f"- Total Rows (sum of tables): {total_rows}")
        lines.append("")
        lines.append("### Tables")
        lines.append("- Schema | Table | Columns | Rows")
        lines.append("- --- | --- | --- | ---")
        for t in res['tables']:
            lines.append(f"- {t['schema']} | {t['table']} | {t['columns']} | {t['rows']}")
        lines.append("")

    out_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Audit PostgreSQL table/column/row counts across GenIMS databases.")
    parser.add_argument('--row-method', choices=['exact','estimate'], default='exact',
                        help="Use 'exact' (COUNT(*)) or 'estimate' (pg_class.reltuples). Exact can be slower.")
    parser.add_argument('--output', default=str(REPO_ROOT / 'Database_Audit_Report.md'),
                        help='Path to Markdown report output file.')
    args = parser.parse_args()

    dbnames = list(DATABASES.keys())
    results = []
    for db in dbnames:
        print(f"Auditing {db} ...")
        try:
            res = audit_database(db, args.row_method)
            print(f"  Tables: {res['tables_total']}, Columns: {res['columns_total']}, Rows(sum): {sum(t['rows'] for t in res['tables'])}")
            results.append(res)
        except Exception as e:
            print(f"  ERROR auditing {db}: {e}")

    out_path = Path(args.output)
    write_markdown_report(results, out_path, args.row_method)
    print(f"\nReport written to: {out_path}")


if __name__ == '__main__':
    main()
